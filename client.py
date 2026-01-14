from __future__ import annotations

import argparse
import socket
import sys
import time
from typing import Optional, Tuple

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
    S2C_PAYLOAD_SIZE,
    pack_request,
    unpack_offer,
    unpack_server_payload,
    pack_client_payload,
)
from cards import Card, hand_total, RANK_NAMES, SUIT_NAMES

def parse_rounds(inp: str) -> int:
    try:
        n = int(inp.strip())
    except Exception:
        raise ValueError("Please enter a number (1-255)")
    if not (1 <= n <= 255):
        raise ValueError("Rounds must be between 1 and 255")
    return n

def pretty_card(rank: int, suit: int) -> str:
    r = RANK_NAMES.get(rank, str(rank))
    s = SUIT_NAMES[suit] if 0 <= suit <= 3 else f"Suit{suit}"
    return f"{r} of {s}"

def decision_to_wire(dec: str) -> bytes:
    d = dec.strip().lower()
    if d in ("h", "hit"):
        return b"Hittt"
    if d in ("s", "stand"):
        return b"Stand"
    raise ValueError("Enter 'hit' (h) or 'stand' (s)")

def listen_for_offer(udp_sock: socket.socket, timeout: float = 0.0) -> Tuple[str, int, str]:
    """Return (server_ip, tcp_port, server_name) for first valid offer."""
    if timeout:
        udp_sock.settimeout(timeout)
    else:
        udp_sock.settimeout(None)

    while True:
        data, addr = udp_sock.recvfrom(4096)
        try:
            offer = unpack_offer(data[:OFFER_SIZE])
        except Exception:
            continue
        server_ip = addr[0]
        return server_ip, offer.tcp_port, offer.server_name

def play_session(server_ip: str, tcp_port: int, client_name: str, rounds: int, connect_timeout: float) -> None:
    log("CLIENT", f"Connecting to {server_ip}:{tcp_port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(connect_timeout)
    s.connect((server_ip, tcp_port))
    s.settimeout(10.0)

    # Send request
    s.sendall(pack_request(rounds, client_name))

    wins = losses = ties = 0

    for r in range(1, rounds + 1):
        log("CLIENT", f"=== Round {r}/{rounds} ===")

        # Initial deal: expect 3 cards (player, player, dealer up)
        player: list[tuple[int,int]] = []
        dealer: list[tuple[int,int]] = []

        for i in range(3):
            p = unpack_server_payload(recv_exact(s, S2C_PAYLOAD_SIZE))
            player_or_dealer_card = (p.card.rank, p.card.suit)
            if i < 2:
                player.append(player_or_dealer_card)
                log("CLIENT", f"You got: {pretty_card(*player_or_dealer_card)}")
            else:
                dealer.append(player_or_dealer_card)
                log("CLIENT", f"Dealer shows: {pretty_card(*player_or_dealer_card)}")

        def total_with_aces(cards: list[tuple[int,int]]) -> int:
            """Compute blackjack total with flexible Ace handling for (rank, suit) tuples."""
            total = 0
            aces = 0
            for r, _ in cards:
                if r == 1:
                    total += 11
                    aces += 1
                elif 2 <= r <= 10:
                    total += r
                else:
                    total += 10

            while total > 21 and aces > 0:
                total -= 10
                aces -= 1

            return total

        def player_total() -> int:
            return total_with_aces(player)

        # Player turn
        while True:
            pt = player_total()
            if pt > 21:
                # In theory server would already have sent LOSS on bust-hit,
                # but handle defensively.
                log("CLIENT", f"You bust with {pt}")
                losses += 1
                break

            while True:
                try:
                    dec = input(f"Your total = {pt}. Hit or stand? ").strip()
                    decision5 = decision_to_wire(dec)
                    break
                except ValueError as e:
                    print(e)

            s.sendall(pack_client_payload(decision5))

            if decision5 == b"Stand":
                break

            # Receive server response to Hit: either a card (not-over) or final (loss)
            p = unpack_server_payload(recv_exact(s, S2C_PAYLOAD_SIZE))
            player.append((p.card.rank, p.card.suit))
            log("CLIENT", f"You drew: {pretty_card(p.card.rank, p.card.suit)}")

            if p.result == RESULT_LOSS:
                log("CLIENT", "You busted. Dealer wins.")
                losses += 1
                # Round over immediately (server won't send more for this round)
                break
            # else round continues

        # If bust, continue next round
        if len(player) and player_total() > 21:
            continue

        # Dealer turn: first message should reveal hidden card
        p = unpack_server_payload(recv_exact(s, S2C_PAYLOAD_SIZE))
        dealer.append((p.card.rank, p.card.suit))
        log("CLIENT", f"Dealer reveals: {pretty_card(p.card.rank, p.card.suit)}")
        dealer_total = lambda: total_with_aces(dealer)

        # Then dealer may send more not-over cards, followed by a final result message.
        while True:
            p = unpack_server_payload(recv_exact(s, S2C_PAYLOAD_SIZE))
            if p.result == RESULT_NOT_OVER:
                dealer.append((p.card.rank, p.card.suit))
                log("CLIENT", f"Dealer draws: {pretty_card(p.card.rank, p.card.suit)} (dealer total {dealer_total()})")
                continue

            # Final result
            pt = player_total()
            dt = dealer_total()
            if p.result == RESULT_WIN:
                log("CLIENT", f"You win! (you {pt} vs dealer {dt})")
                wins += 1
            elif p.result == RESULT_LOSS:
                log("CLIENT", f"You lose. (you {pt} vs dealer {dt})")
                losses += 1
            else:
                log("CLIENT", f"Tie. (you {pt} vs dealer {dt})")
                ties += 1
            break

    safe_close(s)

    total = wins + losses + ties
    win_rate = (wins / total) if total else 0.0
    print(f"Finished playing {total} rounds, win rate: {win_rate:.2%} (W/L/T={wins}/{losses}/{ties})", flush=True)

def main() -> None:
    ap = argparse.ArgumentParser(description="Blackjack hackathon client (listen UDP offers + play over TCP)")
    ap.add_argument("--name", default="Client", help="team/client name (max 32 bytes on wire)")
    ap.add_argument("--udp-port", type=int, default=UDP_OFFER_PORT_DEFAULT, help="UDP offer port (default 13122)")
    ap.add_argument("--connect-timeout", type=float, default=4.0, help="TCP connect timeout seconds")
    args = ap.parse_args()

    # UDP socket for offers
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # SO_REUSEPORT helps running multiple clients on same machine (if supported)
    try:
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except Exception:
        pass
    udp.bind(("", args.udp_port))

    log("CLIENT", f"Client started, listening for offer requests on UDP {args.udp_port}...")

    try:
        while True:
            # Ask for rounds first (per example flow)
            while True:
                try:
                    rounds = parse_rounds(input("How many rounds do you want to play? "))
                    break
                except ValueError as e:
                    print(e)

            server_ip, tcp_port, server_name = listen_for_offer(udp)
            log("CLIENT", f"Received offer from {server_ip} (server name: '{server_name}', tcp port {tcp_port})")

            try:
                play_session(server_ip, tcp_port, args.name, rounds, args.connect_timeout)
            except Exception as e:
                log("CLIENT", f"Session error: {e}")
                time.sleep(0.5)  # short backoff
            log("CLIENT", "Returning to offer listening...")

    except KeyboardInterrupt:
        log("CLIENT", "Bye")
    finally:
        safe_close(udp)

if __name__ == "__main__":
    main()
