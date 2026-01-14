from __future__ import annotations

import argparse
import socket
import threading
import time
from typing import Tuple

from common import (
    UDP_OFFER_PORT_DEFAULT,
    log,
    safe_close,
    recv_exact,
    RESULT_NOT_OVER,
    RESULT_TIE,
    RESULT_LOSS,
    RESULT_WIN,
)
from protocol import (
    OFFER_SIZE,
    REQUEST_SIZE,
    C2S_PAYLOAD_SIZE,
    S2C_PAYLOAD_SIZE,
    pack_offer,
    unpack_request,
    unpack_client_payload,
    pack_server_payload,
)
from cards import Deck, Card, hand_total

def pick_bind_ip() -> str:
    """Best-effort local IP detection for pretty printing."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"

class OfferBroadcaster(threading.Thread):
    def __init__(self, server_name: str, tcp_port: int, udp_port: int, interval: float) -> None:
        super().__init__(daemon=True)
        self.server_name = server_name
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.interval = interval
        self._stop = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self) -> None:
        payload = pack_offer(self.tcp_port, self.server_name)
        dst = ("<broadcast>", self.udp_port)
        while not self._stop.is_set():
            try:
                self.sock.sendto(payload, dst)
            except Exception as e:
                log("SERVER", f"Offer broadcast failed: {e}")
            self._stop.wait(self.interval)

    def stop(self) -> None:
        self._stop.set()
        safe_close(self.sock)

def decide_winner(player_total: int, dealer_total: int, player_bust: bool, dealer_bust: bool) -> int:
    if player_bust:
        return RESULT_LOSS
    if dealer_bust:
        return RESULT_WIN
    if player_total > dealer_total:
        return RESULT_WIN
    if dealer_total > player_total:
        return RESULT_LOSS
    return RESULT_TIE

def send_card(conn: socket.socket, result: int, card: Card) -> None:
    msg = pack_server_payload(result, card.rank, card.suit)
    conn.sendall(msg)

def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    ip, port = addr
    prefix = f"CLIENT {ip}:{port}"

    try:
        conn.settimeout(10.0)
        req_raw = recv_exact(conn, REQUEST_SIZE)
        req = unpack_request(req_raw)
        rounds = req.rounds
        log("SERVER", f"{prefix} connected as '{req.client_name}', requested {rounds} rounds")

        wins = losses = ties = 0

        for r in range(1, rounds + 1):
            deck = Deck()  # fresh deck each round
            player = [deck.draw(), deck.draw()]
            dealer = [deck.draw(), deck.draw()]
            player_bust = dealer_bust = False

            log("SERVER", f"{prefix} Round {r}/{rounds} start")
            # Initial deal: send player's 2 cards and dealer's first card (face-up)
            send_card(conn, RESULT_NOT_OVER, player[0])
            send_card(conn, RESULT_NOT_OVER, player[1])
            send_card(conn, RESULT_NOT_OVER, dealer[0])

            # Player turn
            while True:
                pt = hand_total(player)
                if pt > 21:
                    player_bust = True
                    log("SERVER", f"{prefix} player bust with {pt}")
                    break

                # Receive decision
                try:
                    decision_raw = recv_exact(conn, C2S_PAYLOAD_SIZE)
                except ConnectionError:
                    raise
                decision = unpack_client_payload(decision_raw)

                if decision == "Hittt":
                    c = deck.draw()
                    player.append(c)
                    pt = hand_total(player)
                    log("SERVER", f"{prefix} player HIT -> {c.short()} (total {pt})")
                    # If bust, send final immediately with loss; else not-over
                    if pt > 21:
                        player_bust = True
                        send_card(conn, RESULT_LOSS, c)
                        log("SERVER", f"{prefix} sent LOSS")
                        break
                    else:
                        send_card(conn, RESULT_NOT_OVER, c)
                elif decision == "Stand":
                    log("SERVER", f"{prefix} player STAND (total {pt})")
                    break
                else:
                    # Unknown decision: treat as Stand (defensive compatibility)
                    log("SERVER", f"{prefix} unknown decision '{decision}', treating as STAND")
                    break

            if player_bust:
                losses += 1
                continue

            # Dealer turn: reveal hidden card first
            send_card(conn, RESULT_NOT_OVER, dealer[1])
            dt = hand_total(dealer)
            log("SERVER", f"{prefix} dealer reveals {dealer[1].short()} (total {dt})")

            last_dealer_card = dealer[1]

            while dt < 17:
                c = deck.draw()
                dealer.append(c)
                last_dealer_card = c
                dt = hand_total(dealer)
                log("SERVER", f"{prefix} dealer HIT -> {c.short()} (total {dt})")
                if dt > 21:
                    dealer_bust = True
                    break
                send_card(conn, RESULT_NOT_OVER, c)

            pt = hand_total(player)
            dt = hand_total(dealer)
            result = decide_winner(pt, dt, player_bust, dealer_bust)
            if result == RESULT_WIN:
                wins += 1
            elif result == RESULT_LOSS:
                losses += 1
            else:
                ties += 1

            # Final result message: include last relevant dealer card (or dealer[0] if no draws)
            final_card = last_dealer_card if dealer else dealer[0]
            send_card(conn, result, final_card)
            log("SERVER", f"{prefix} Round {r} result: player {pt}, dealer {dt} -> {result}")

        log("SERVER", f"{prefix} finished: W/L/T = {wins}/{losses}/{ties}")
    except Exception as e:
        log("SERVER", f"{prefix} error: {e}")
    finally:
        safe_close(conn)
        log("SERVER", f"{prefix} disconnected")

def main() -> None:
    ap = argparse.ArgumentParser(description="Blackjack hackathon server (UDP offers + TCP game)")
    ap.add_argument("--name", default="Server", help="team/server name (max 32 bytes on wire)")
    ap.add_argument("--tcp-port", type=int, default=0, help="TCP listen port (0 = auto)")
    ap.add_argument("--udp-port", type=int, default=UDP_OFFER_PORT_DEFAULT, help="UDP offer port (default 13122)")
    ap.add_argument("--offer-interval", type=float, default=1.0, help="seconds between UDP offers")
    args = ap.parse_args()

    # TCP listen socket
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp.bind(("", args.tcp_port))
    tcp.listen()
    tcp_port = tcp.getsockname()[1]

    ip = pick_bind_ip()
    log("SERVER", f"Server started, listening on IP address {ip}, TCP port {tcp_port}")

    broadcaster = OfferBroadcaster(args.name, tcp_port, args.udp_port, args.offer_interval)
    broadcaster.start()
    log("SERVER", f"Broadcasting offers on UDP {args.udp_port} every {args.offer_interval:.1f}s")

    try:
        while True:
            conn, addr = tcp.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        log("SERVER", "Shutting down...")
    finally:
        broadcaster.stop()
        safe_close(tcp)

if __name__ == "__main__":
    main()
