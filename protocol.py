"""Binary protocol packing/unpacking.

All formats are described in the assignment PDF. fileciteturn0file0
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Tuple

from common import (
    MAGIC_COOKIE,
    MSG_OFFER,
    MSG_REQUEST,
    MSG_PAYLOAD,
    NAME_LEN,
    clamp_name,
    unpad_name,
)

# Sizes (bytes)
OFFER_SIZE = 4 + 1 + 2 + NAME_LEN      # 39
REQUEST_SIZE = 4 + 1 + 1 + NAME_LEN    # 38
C2S_PAYLOAD_SIZE = 4 + 1 + 5           # 10
S2C_PAYLOAD_SIZE = 4 + 1 + 1 + 3       # 9

# Suit encoding: 0..3 = H,D,C,S
SUITS = ("H", "D", "C", "S")

@dataclass(frozen=True)
class Offer:
    tcp_port: int
    server_name: str

@dataclass(frozen=True)
class Request:
    rounds: int
    client_name: str

@dataclass(frozen=True)
class CardWire:
    rank: int  # 1..13
    suit: int  # 0..3

@dataclass(frozen=True)
class ServerPayload:
    result: int  # 0..3
    card: CardWire

def pack_offer(tcp_port: int, server_name: str) -> bytes:
    pass

def unpack_offer(data: bytes) -> Offer:
    pass
    

def pack_request(rounds: int, client_name: str) -> bytes:
    pass
    

def unpack_request(data: bytes) -> Request:
    pass
    

def pack_client_payload(decision5: bytes) -> bytes:
    pass

def unpack_client_payload(data: bytes) -> str:
    pass

def pack_server_payload(result: int, rank: int, suit: int) -> bytes:
    pass

def unpack_server_payload(data: bytes) -> ServerPayload:
    pass