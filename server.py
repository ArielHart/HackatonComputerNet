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
    pass

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
        pass

    def stop(self) -> None:
        pass 

def decide_winner(player_total: int, dealer_total: int, player_bust: bool, dealer_bust: bool) -> int:
    pass

def send_card(conn: socket.socket, result: int, card: Card) -> None:
    pass

def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    pass

def main() -> None:
    pass
