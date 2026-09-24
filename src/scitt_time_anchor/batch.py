"""Section 4.3 deterministic batch-path construction.

Calendar submission and .ots commitment merging are intentionally outside this
module.  Their wire protocol is imported by the draft from OpenTimestamps and
is not part of the normative VERIFY-ANCHOR procedure.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


_HASH_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class PathOperation:
    name: str
    argument: bytes | None = None


@dataclass(frozen=True, slots=True)
class BatchPath:
    claimed_hash: str
    nonce: bytes
    leaf: bytes
    operations: tuple[PathOperation, ...]


@dataclass(frozen=True, slots=True)
class BatchResult:
    merkle_root: bytes
    paths: tuple[BatchPath, ...]


@dataclass(slots=True)
class _WorkingPath:
    claimed_hash: str
    nonce: bytes
    leaf: bytes
    operations: list[PathOperation]


def _sha256(value: bytes) -> bytes:
    return hashlib.sha256(value).digest()


def build_batch_paths(
    claimed_hashes: Sequence[str] | Iterable[str],
    *,
    nonces: Sequence[bytes] | None = None,
    random_bytes: Callable[[int], bytes] = os.urandom,
) -> BatchResult:
    """Apply Section 4.3 steps 1-3 and return per-origin recorded paths.

    ``nonces`` is solely a deterministic test/vector hook.  Production callers
    should omit it so each leaf receives a fresh 16-byte OS-random nonce.
    """

    hashes = tuple(claimed_hashes)
    if not hashes:
        raise ValueError("origin_list must contain at least one origin")
    for claimed in hashes:
        if not isinstance(claimed, str) or _HASH_RE.fullmatch(claimed) is None:
            raise ValueError("origin hash must match /^(sha256:)?[0-9a-f]{64}$/")

    if nonces is not None and len(nonces) != len(hashes):
        raise ValueError("nonces must have one entry per origin")

    working: list[_WorkingPath] = []
    for index, claimed in enumerate(hashes):
        digest = bytes.fromhex(claimed.removeprefix("sha256:"))
        nonce = nonces[index] if nonces is not None else random_bytes(16)
        if not isinstance(nonce, bytes) or len(nonce) != 16:
            raise ValueError("each blinding nonce must be exactly 16 bytes")
        leaf = _sha256(digest + nonce)
        working.append(
            _WorkingPath(
                claimed_hash=claimed,
                nonce=nonce,
                leaf=leaf,
                operations=[PathOperation("append", nonce), PathOperation("sha256")],
            )
        )

    level = [item.leaf for item in working]
    members: list[list[int]] = [[i] for i in range(len(working))]
    while len(level) > 1:
        next_level: list[bytes] = []
        next_members: list[list[int]] = []
        paired_end = len(level) - (len(level) % 2)
        for index in range(0, paired_end, 2):
            left = level[index]
            right = level[index + 1]
            for origin_index in members[index]:
                working[origin_index].operations.extend(
                    (PathOperation("append", right), PathOperation("sha256"))
                )
            for origin_index in members[index + 1]:
                working[origin_index].operations.extend(
                    (PathOperation("prepend", left), PathOperation("sha256"))
                )
            next_level.append(_sha256(left + right))
            next_members.append(members[index] + members[index + 1])
        if len(level) % 2:
            next_level.append(level[-1])
            next_members.append(members[-1])
        level = next_level
        members = next_members

    return BatchResult(
        merkle_root=level[0],
        paths=tuple(
            BatchPath(
                claimed_hash=item.claimed_hash,
                nonce=item.nonce,
                leaf=item.leaf,
                operations=tuple(item.operations),
            )
            for item in working
        ),
    )
