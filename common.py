"""Shared constants and helper utilities."""

from __future__ import annotations

import socket
import struct
import sys
import time
from dataclasses import dataclass
from typing import Optional

MAGIC_COOKIE = 0xABCDDCBA

# Message types
MSG_OFFER = 0x02
MSG_REQUEST = 0x03
MSG_PAYLOAD = 0x04

# Result codes (server -> client)
RESULT_NOT_OVER = 0x00
RESULT_TIE = 0x01
RESULT_LOSS = 0x02
RESULT_WIN = 0x03

UDP_OFFER_PORT_DEFAULT = 13122

NAME_LEN = 32

def now_ts() -> str:
    return time.strftime("%H:%M:%S", time.localtime())

def log(prefix: str, msg: str) -> None:
    print(f"[{now_ts()}] {prefix}: {msg}", flush=True)

def clamp_name(name: str) -> bytes:
    pass

def unpad_name(raw32: bytes) -> str:
    pass

def recv_exact(sock: socket.socket, n: int) -> bytes:
    pass

def safe_close(sock: Optional[socket.socket]) -> None:
    pass
