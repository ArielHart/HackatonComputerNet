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
    pass

def pretty_card(rank: int, suit: int) -> str:
    pass

def decision_to_wire(dec: str) -> bytes:
    pass

def listen_for_offer(udp_sock: socket.socket, timeout: float = 0.0) -> Tuple[str, int, str]:
    pass

def play_session(server_ip: str, tcp_port: int, client_name: str, rounds: int, connect_timeout: float) -> None:
    pass

def main() -> None:
    pass
