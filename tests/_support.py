from __future__ import annotations

import hashlib

from scitt_time_anchor.model import BlockHeader
from scitt_time_anchor.ots import (
    BITCOIN_ATTESTATION_TAG,
    HEADER_MAGIC,
    PENDING_ATTESTATION_TAG,
)


def varuint(value: int) -> bytes:
    if value < 0:
        raise ValueError
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        result.append(byte)
        if not value:
            return bytes(result)


def varbytes(value: bytes) -> bytes:
    return varuint(len(value)) + value


def bitcoin_attestation(height: int) -> bytes:
    return b"\x00" + BITCOIN_ATTESTATION_TAG + varbytes(varuint(height))


def pending_attestation(uri: str) -> bytes:
    payload = varbytes(uri.encode("ascii"))
    return b"\x00" + PENDING_ATTESTATION_TAG + varbytes(payload)


def detached(message: bytes, timestamp: bytes, *, hash_tag: int = 0x08) -> bytes:
    return HEADER_MAGIC + b"\x01" + bytes((hash_tag,)) + message + timestamp


def header(merkle_root: bytes, ntime: int = 1_783_591_379) -> BlockHeader:
    if len(merkle_root) != 32:
        raise ValueError
    return BlockHeader(bytes(36) + merkle_root + ntime.to_bytes(4, "little") + bytes(8))


class MemoryHeaderSource:
    def __init__(self, headers=None, confirmations=6):
        self.headers = dict(headers or {})
        self.confirmations = confirmations
        self.header_calls: list[int] = []
        self.confirmation_calls: list[int] = []

    def header_by_height(self, height: int):
        self.header_calls.append(height)
        return self.headers.get(height)

    def confirmations_on(self, height: int):
        self.confirmation_calls.append(height)
        if isinstance(self.confirmations, dict):
            return self.confirmations.get(height)
        return self.confirmations


def digest_path(message: bytes, suffix: bytes) -> bytes:
    return hashlib.sha256(message + suffix).digest()
