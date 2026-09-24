"""OpenTimestamps v0.4.5 detached-proof parser and profile replay.

The accepted wire grammar, limits, tag values, duplicate handling, and
recursion limit are transcribed from commit
``a90094e3ca9a8229abd016be8816d7b90b9fd1e6``.  No OpenTimestamps package is
loaded at runtime.
"""

from __future__ import annotations

import binascii
import hashlib
from dataclasses import dataclass, field


HEADER_MAGIC = b"\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94"
MAJOR_VERSION = 1
BITCOIN_ATTESTATION_TAG = bytes.fromhex("0588960d73d71901")
LITECOIN_ATTESTATION_TAG = bytes.fromhex("06869a0d73d71b45")
ETHEREUM_ATTESTATION_TAG = bytes.fromhex("30fe8087b5c7ead7")
PENDING_ATTESTATION_TAG = bytes.fromhex("83dfe30d2ef90c8e")
MAX_ATTESTATION_PAYLOAD = 8192
MAX_URI_LENGTH = 1000
MAX_OP_LENGTH = 4096
TIMESTAMP_RECURSION_LIMIT = 256

_PENDING_URI_CHARS = frozenset(
    b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._/:"
)
_INITIAL_HASH_OPS: dict[int, tuple[str, int]] = {
    0x02: ("sha1", 20),
    0x03: ("ripemd160", 20),
    0x08: ("sha256", 32),
    0x67: ("keccak256", 32),
}
_UNARY_OPS: dict[int, str] = {
    0x02: "sha1",
    0x03: "ripemd160",
    0x08: "sha256",
    0x67: "keccak256",
    0xF2: "reverse",
    0xF3: "hexlify",
}
_BINARY_OPS: dict[int, str] = {0xF0: "append", 0xF1: "prepend"}


class OTSParseError(ValueError):
    """The byte stream is not a v0.4.5 detached timestamp proof."""


@dataclass(frozen=True, slots=True)
class Operation:
    name: str
    argument: bytes | None = None


@dataclass(frozen=True, slots=True)
class BitcoinBranch:
    height: int
    operations: tuple[Operation, ...]

    def replay_sha256_profile(self, initial: bytes) -> bytes | None:
        """Replay a branch under the operation subset allowed by Section 1.4."""

        running = initial
        for operation in self.operations:
            if operation.name == "append" and operation.argument is not None:
                running = running + operation.argument
            elif operation.name == "prepend" and operation.argument is not None:
                running = operation.argument + running
            elif operation.name == "sha256" and operation.argument is None:
                running = hashlib.sha256(running).digest()
            else:
                return None
            if not running or len(running) > MAX_OP_LENGTH:
                return None
        return running


@dataclass(frozen=True, slots=True)
class ParsedProof:
    file_hash_operation: str
    message: bytes
    bitcoin_branches: tuple[BitcoinBranch, ...]
    pending_calendar_urls: tuple[str, ...]
    attestation_count: int


@dataclass(frozen=True, slots=True)
class _MessageState:
    length: int
    value: bytes | None


@dataclass(frozen=True, slots=True)
class _Attestation:
    kind: str
    tag: bytes
    payload: bytes
    value: int | str | None = None

    @property
    def duplicate_key(self) -> tuple[object, ...]:
        if self.kind == "unknown":
            return (self.kind, self.tag, self.payload)
        return (self.kind, self.value)


@dataclass(slots=True)
class _Node:
    attestations: dict[tuple[object, ...], _Attestation] = field(default_factory=dict)
    children: dict[Operation, "_Node"] = field(default_factory=dict)


class _Cursor:
    __slots__ = ("data", "offset")

    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def read(self, length: int) -> bytes:
        end = self.offset + length
        if length < 0 or end > len(self.data):
            available = max(0, len(self.data) - self.offset)
            raise OTSParseError(
                f"truncated data: needed {length} bytes, only {available} remain"
            )
        result = self.data[self.offset:end]
        self.offset = end
        return result

    def read_byte(self) -> int:
        return self.read(1)[0]

    def read_varuint(self) -> int:
        # Unsigned little-endian base-128, matching v0.4.5.  That release does
        # not reject non-minimal encodings, so neither does this parser.
        value = 0
        shift = 0
        while True:
            byte = self.read_byte()
            value |= (byte & 0x7F) << shift
            if not byte & 0x80:
                return value
            shift += 7

    def read_varbytes(self, max_length: int, *, min_length: int = 0) -> bytes:
        length = self.read_varuint()
        if length > max_length:
            raise OTSParseError(
                f"variable byte string exceeds limit: {length} > {max_length}"
            )
        if length < min_length:
            raise OTSParseError(
                f"variable byte string shorter than limit: {length} < {min_length}"
            )
        return self.read(length)

    def assert_eof(self) -> None:
        if self.offset != len(self.data):
            raise OTSParseError("trailing garbage after deserialized object")


def _parse_operation(cursor: _Cursor, tag: int) -> Operation:
    if tag in _BINARY_OPS:
        return Operation(
            _BINARY_OPS[tag],
            cursor.read_varbytes(MAX_OP_LENGTH, min_length=1),
        )
    if tag in _UNARY_OPS:
        return Operation(_UNARY_OPS[tag])
    raise OTSParseError(f"unknown operation tag 0x{tag:02x}")


def _operation_result(operation: Operation, state: _MessageState) -> _MessageState:
    if state.length > MAX_OP_LENGTH:
        raise OTSParseError("operation input exceeds v0.4.5 message limit")

    if operation.name in ("append", "prepend"):
        assert operation.argument is not None
        result_length = state.length + len(operation.argument)
        if result_length > MAX_OP_LENGTH:
            raise OTSParseError("operation result exceeds v0.4.5 result limit")
        if state.value is None:
            value = None
        elif operation.name == "append":
            value = state.value + operation.argument
        else:
            value = operation.argument + state.value
        return _MessageState(result_length, value)

    if operation.name == "reverse":
        if state.length == 0:
            raise OTSParseError("reverse cannot operate on an empty message")
        return _MessageState(
            state.length, None if state.value is None else state.value[::-1]
        )

    if operation.name == "hexlify":
        if state.length > MAX_OP_LENGTH // 2:
            raise OTSParseError("hexlify input exceeds v0.4.5 message limit")
        if state.length == 0:
            raise OTSParseError("hexlify cannot operate on an empty message")
        return _MessageState(
            state.length * 2,
            None if state.value is None else binascii.hexlify(state.value),
        )

    if operation.name == "sha256":
        return _MessageState(
            32,
            None if state.value is None else hashlib.sha256(state.value).digest(),
        )
    if operation.name == "sha1":
        return _MessageState(
            20, None if state.value is None else hashlib.sha1(state.value).digest()
        )
    if operation.name == "ripemd160":
        # Exact bytes are unnecessary after an operation unsupported by this
        # profile.  The length is sufficient to reproduce all parser limits.
        return _MessageState(20, None)
    if operation.name == "keccak256":
        # v0.4.5 delegates Keccak to pycryptodomex.  This profile must classify
        # the branch unsupported, so only its fixed result length is needed to
        # deserialize descendants without adding a runtime dependency.
        return _MessageState(32, None)
    raise AssertionError(f"unhandled operation {operation.name}")


def _parse_known_height_payload(payload: bytes) -> int:
    payload_cursor = _Cursor(payload)
    height = payload_cursor.read_varuint()
    payload_cursor.assert_eof()
    return height


def _parse_attestation(cursor: _Cursor) -> _Attestation:
    tag = cursor.read(8)
    payload = cursor.read_varbytes(MAX_ATTESTATION_PAYLOAD)

    if tag == BITCOIN_ATTESTATION_TAG:
        return _Attestation(
            "bitcoin", tag, payload, _parse_known_height_payload(payload)
        )
    if tag == LITECOIN_ATTESTATION_TAG:
        return _Attestation(
            "litecoin", tag, payload, _parse_known_height_payload(payload)
        )
    if tag == ETHEREUM_ATTESTATION_TAG:
        return _Attestation(
            "ethereum", tag, payload, _parse_known_height_payload(payload)
        )
    if tag == PENDING_ATTESTATION_TAG:
        payload_cursor = _Cursor(payload)
        uri_bytes = payload_cursor.read_varbytes(MAX_URI_LENGTH)
        payload_cursor.assert_eof()
        if any(byte not in _PENDING_URI_CHARS for byte in uri_bytes):
            raise OTSParseError("pending-attestation URI contains a forbidden byte")
        uri = uri_bytes.decode("ascii")
        return _Attestation("pending", tag, payload, uri)
    return _Attestation("unknown", tag, payload)


def _parse_timestamp(
    cursor: _Cursor, state: _MessageState, recursion_remaining: int
) -> _Node:
    if recursion_remaining == 0:
        raise OTSParseError("v0.4.5 timestamp recursion limit reached")
    node = _Node()

    def parse_element(tag: int) -> None:
        if tag == 0x00:
            attestation = _parse_attestation(cursor)
            node.attestations[attestation.duplicate_key] = attestation
            return
        operation = _parse_operation(cursor, tag)
        child_state = _operation_result(operation, state)
        child = _parse_timestamp(cursor, child_state, recursion_remaining - 1)
        # OpSet in v0.4.5 overwrites a duplicate operation after consuming it.
        node.children[operation] = child

    tag = cursor.read_byte()
    while tag == 0xFF:
        parse_element(cursor.read_byte())
        tag = cursor.read_byte()
    parse_element(tag)
    return node


def _flatten(root: _Node) -> tuple[tuple[BitcoinBranch, ...], tuple[str, ...], int]:
    branches: list[BitcoinBranch] = []
    pending_urls: list[str] = []
    attestation_count = 0

    def walk(node: _Node, path: tuple[Operation, ...]) -> None:
        nonlocal attestation_count
        for attestation in node.attestations.values():
            attestation_count += 1
            if attestation.kind == "bitcoin":
                assert isinstance(attestation.value, int)
                branches.append(BitcoinBranch(attestation.value, path))
            elif attestation.kind == "pending":
                assert isinstance(attestation.value, str)
                pending_urls.append(attestation.value)
        for operation, child in node.children.items():
            walk(child, path + (operation,))

    walk(root, ())
    return tuple(branches), tuple(pending_urls), attestation_count


def parse_detached_timestamp(data: bytes) -> ParsedProof:
    """Parse an OpenTimestamps detached proof as serialized by v0.4.5."""

    if not isinstance(data, bytes):
        raise OTSParseError("proof must be a bytes object")
    cursor = _Cursor(data)
    if cursor.read(len(HEADER_MAGIC)) != HEADER_MAGIC:
        raise OTSParseError("incorrect OpenTimestamps detached-proof magic")
    major_version = cursor.read_varuint()
    if major_version != MAJOR_VERSION:
        raise OTSParseError(f"unsupported detached-proof major version {major_version}")

    initial_tag = cursor.read_byte()
    try:
        file_hash_operation, digest_length = _INITIAL_HASH_OPS[initial_tag]
    except KeyError as error:
        raise OTSParseError(
            f"unknown detached-file hash operation 0x{initial_tag:02x}"
        ) from error
    message = cursor.read(digest_length)
    root = _parse_timestamp(
        cursor,
        _MessageState(len(message), message),
        TIMESTAMP_RECURSION_LIMIT,
    )
    cursor.assert_eof()
    bitcoin_branches, pending_urls, attestation_count = _flatten(root)
    return ParsedProof(
        file_hash_operation=file_hash_operation,
        message=message,
        bitcoin_branches=bitcoin_branches,
        pending_calendar_urls=pending_urls,
        attestation_count=attestation_count,
    )
