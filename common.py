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
    return time.strftime("%H:%M:%S")

def log(prefix: str, msg: str) -> None:
    print(f"[{now_ts()}] {prefix}: {msg}", flush=True)

def clamp_name(name: str) -> bytes:
    """Encode name to fixed 32 bytes, zero padded (truncate if needed)."""
    raw = name.encode("utf-8", errors="ignore")
    if len(raw) > NAME_LEN:
        raw = raw[:NAME_LEN]
    return raw.ljust(NAME_LEN, b"\x00")

def unpad_name(raw32: bytes) -> str:
    return raw32.split(b"\x00", 1)[0].decode("utf-8", errors="replace")

def recv_exact(sock: socket.socket, n: int) -> bytes:
    """Receive exactly n bytes or raise ConnectionError."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf.extend(chunk)
    return bytes(buf)

def safe_close(sock: Optional[socket.socket]) -> None:
    if not sock:
        return
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    try:
        sock.close()
    except Exception:
        pass
