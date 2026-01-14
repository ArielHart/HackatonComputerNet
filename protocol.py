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
    return struct.pack("!IBH", MAGIC_COOKIE, MSG_OFFER, tcp_port) + clamp_name(server_name)

def unpack_offer(data: bytes) -> Offer:
    if len(data) != OFFER_SIZE:
        raise ValueError("bad offer size")
    cookie, mtype, tcp_port = struct.unpack("!IBH", data[:7])
    if cookie != MAGIC_COOKIE or mtype != MSG_OFFER:
        raise ValueError("bad offer header")
    name = unpad_name(data[7:7+NAME_LEN])
    return Offer(tcp_port=tcp_port, server_name=name)

def pack_request(rounds: int, client_name: str) -> bytes:
    if not (1 <= rounds <= 255):
        raise ValueError("rounds must be 1..255")
    return struct.pack("!IBB", MAGIC_COOKIE, MSG_REQUEST, rounds) + clamp_name(client_name)

def unpack_request(data: bytes) -> Request:
    if len(data) != REQUEST_SIZE:
        raise ValueError("bad request size")
    cookie, mtype, rounds = struct.unpack("!IBB", data[:6])
    if cookie != MAGIC_COOKIE or mtype != MSG_REQUEST:
        raise ValueError("bad request header")
    name = unpad_name(data[6:6+NAME_LEN])
    return Request(rounds=rounds, client_name=name)

def pack_client_payload(decision5: bytes) -> bytes:
    if len(decision5) != 5:
        raise ValueError("decision must be 5 bytes")
    return struct.pack("!IB", MAGIC_COOKIE, MSG_PAYLOAD) + decision5

def unpack_client_payload(data: bytes) -> str:
    if len(data) != C2S_PAYLOAD_SIZE:
        raise ValueError("bad c2s payload size")
    cookie, mtype = struct.unpack("!IB", data[:5])
    if cookie != MAGIC_COOKIE or mtype != MSG_PAYLOAD:
        raise ValueError("bad payload header")
    decision = data[5:10].decode("ascii", errors="replace")
    return decision

def pack_server_payload(result: int, rank: int, suit: int) -> bytes:
    if not (0 <= result <= 3):
        raise ValueError("result must be 0..3")
    if not (1 <= rank <= 13):
        raise ValueError("rank must be 1..13")
    if not (0 <= suit <= 3):
        raise ValueError("suit must be 0..3")
    # rank is 2 bytes, suit is 1 byte
    card_bytes = struct.pack("!HB", rank, suit)
    return struct.pack("!IBB", MAGIC_COOKIE, MSG_PAYLOAD, result) + card_bytes

def unpack_server_payload(data: bytes) -> ServerPayload:
    if len(data) != S2C_PAYLOAD_SIZE:
        raise ValueError("bad s2c payload size")
    cookie, mtype, result = struct.unpack("!IBB", data[:6])
    if cookie != MAGIC_COOKIE or mtype != MSG_PAYLOAD:
        raise ValueError("bad payload header")
    rank, suit = struct.unpack("!HB", data[6:9])
    return ServerPayload(result=result, card=CardWire(rank=rank, suit=suit))
