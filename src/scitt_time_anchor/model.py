"""Public data model and the independently-validated-header trust boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class Outcome(str, Enum):
    """The exact three-element result set required by Section 3.3."""

    VALID = "valid"
    INVALID = "invalid"
    UNVERIFIABLE = "unverifiable"


@dataclass(frozen=True, slots=True)
class ProofBundle:
    """Section 2.4.3 ProofBundle.

    ``origin_id`` and ``bitcoin_block_height`` are accepted but deliberately
    never consulted by verification.
    """

    ots_proof: bytes
    claimed_hash: str
    origin_id: str | None = None
    bitcoin_block_height: int | None = None


@dataclass(frozen=True, slots=True)
class BlockHeader:
    """An 80-byte Bitcoin block header supplied by a validated source."""

    raw: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.raw, bytes):
            raise TypeError("block header must be bytes")
        if len(self.raw) != 80:
            raise ValueError("Bitcoin block header must be exactly 80 bytes")

    @property
    def merkle_root(self) -> bytes:
        """Header Merkle root in internal/wire byte order."""

        return self.raw[36:68]

    @property
    def ntime(self) -> int:
        """Miner-declared nTime, informative under the profile."""

        return int.from_bytes(self.raw[68:72], "little")


@runtime_checkable
class ValidatedHeaderSource(Protocol):
    """Caller-owned proof that headers belong to the validated most-work chain.

    Implementations MUST return a header only after independently placing it on
    the validated Bitcoin most-work chain, and MUST derive confirmations from
    that same chain.  The verifier can consume this guarantee but cannot infer
    it from 80 raw bytes or from agreement among block explorers.
    """

    def header_by_height(self, height: int) -> BlockHeader | None:
        """Return a validated header at ``height``, or ``None``."""

    def confirmations_on(self, height: int) -> int | None:
        """Count validated blocks at ``height`` and above, including itself."""


@dataclass(frozen=True, slots=True)
class BranchReport:
    """Diagnostic for one Bitcoin-attested proof branch."""

    height: int
    state: str
    operation_count: int


@dataclass(frozen=True, slots=True)
class VerificationReport:
    """A required outcome plus non-normative diagnostic detail.

    ``outcome`` is always exactly one of valid, invalid, or unverifiable.
    Diagnostic fields do not add another verification state.
    """

    outcome: Outcome
    reason: str
    branches: tuple[BranchReport, ...] = ()
    block_height: int | None = None
    reference_wall_clock_projection: int | None = None
    confirmations: int | None = None
