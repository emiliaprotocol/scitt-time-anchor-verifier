"""Normative VERIFY-ANCHOR implementation from Section 3.1."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .model import (
    BlockHeader,
    BranchReport,
    Outcome,
    ProofBundle,
    ValidatedHeaderSource,
    VerificationReport,
)
from .ots import BitcoinBranch, OTSParseError, parse_detached_timestamp


MIN_CONFIRMATIONS = 6


@dataclass(slots=True)
class _EvaluatedBranch:
    branch: BitcoinBranch
    digest: bytes | None
    header: BlockHeader | None
    state: str


def _branch_reports(
    evaluated: list[_EvaluatedBranch],
) -> tuple[BranchReport, ...]:
    return tuple(
        BranchReport(
            height=item.branch.height,
            state=item.state,
            operation_count=len(item.branch.operations),
        )
        for item in evaluated
    )


def verify_anchor(
    artifact_bytes: bytes,
    proof_bundle: ProofBundle,
    header_source: ValidatedHeaderSource,
) -> VerificationReport:
    """Run all eleven VERIFY-ANCHOR steps.

    The source object's contract is the independently validated chain boundary
    from Sections 1.4, 3.1, and 3.2.  A raw header or explorer response is not
    sufficient to instantiate that contract.
    """

    # Step 1: recompute from the original bytes.
    if not isinstance(artifact_bytes, bytes):
        return VerificationReport(Outcome.INVALID, "artifact_bytes is not bytes")
    computed_hash = hashlib.sha256(artifact_bytes).digest()

    # Step 2: the draft defines HEX as lowercase and STRIP-PREFIX as exact.
    if not isinstance(proof_bundle, ProofBundle):
        return VerificationReport(Outcome.INVALID, "proof_bundle has the wrong type")
    claimed_hash = proof_bundle.claimed_hash
    if not isinstance(claimed_hash, str):
        return VerificationReport(Outcome.INVALID, "claimed_hash is not text")
    stripped_claim = (
        claimed_hash[len("sha256:") :]
        if claimed_hash.startswith("sha256:")
        else claimed_hash
    )
    if computed_hash.hex() != stripped_claim:
        return VerificationReport(Outcome.INVALID, "claimed_hash mismatch")

    # Step 3: parse the pinned OTS representation and bind its message.
    try:
        parsed = parse_detached_timestamp(proof_bundle.ots_proof)
    except (OTSParseError, TypeError, ValueError):
        return VerificationReport(Outcome.INVALID, "OTS proof failed to parse")
    # F2 is REQUIRED to be the literal sha256 and maps to the initial 0x08 op.
    if parsed.file_hash_operation != "sha256":
        return VerificationReport(
            Outcome.INVALID, "OTS proof initial hash operation is not sha256"
        )
    if parsed.message != computed_hash:
        return VerificationReport(Outcome.INVALID, "OTS proof message mismatch")

    # Step 4: calendar-only commitments carry no ledger claim yet.
    if not parsed.bitcoin_branches:
        return VerificationReport(
            Outcome.UNVERIFIABLE, "proof carries no Bitcoin attestation"
        )

    # Steps 5-7: keep each replay, height, and independently established header
    # together. Fetch every branch, including a branch whose operations are not
    # in this profile, exactly as the algorithm orders the steps.
    evaluated: list[_EvaluatedBranch] = []
    header_cache: dict[int, BlockHeader | None] = {}
    for branch in parsed.bitcoin_branches:
        digest = branch.replay_sha256_profile(computed_hash)
        if branch.height not in header_cache:
            try:
                candidate = header_source.header_by_height(branch.height)
            except Exception:  # The abstract function returned no usable header.
                candidate = None
            header_cache[branch.height] = (
                candidate if isinstance(candidate, BlockHeader) else None
            )
        header = header_cache[branch.height]
        evaluated.append(_EvaluatedBranch(branch, digest, header, "unclassified"))

    # Step 8: classify per branch and combine without pairing across branches.
    for item in evaluated:
        if item.digest is None:
            item.state = "unsupported"
        elif item.header is None:
            item.state = "unavailable"
        elif item.digest == item.header.merkle_root:
            item.state = "verified"
        else:
            item.state = "mismatched"

    verified = [item for item in evaluated if item.state == "verified"]
    reports = _branch_reports(evaluated)
    if not verified:
        if any(item.state in ("unsupported", "unavailable") for item in evaluated):
            return VerificationReport(
                Outcome.UNVERIFIABLE,
                "no verified branch and at least one branch was unevaluated",
                reports,
            )
        return VerificationReport(
            Outcome.INVALID,
            "every Bitcoin branch mismatched its own block header",
            reports,
        )

    selected = min(verified, key=lambda item: item.branch.height)
    height = selected.branch.height
    assert selected.header is not None

    # Step 9: fixed six-confirmation gate on the same validated chain.
    try:
        confirmations = header_source.confirmations_on(height)
    except Exception:
        confirmations = None
    if isinstance(confirmations, bool) or not isinstance(confirmations, int):
        confirmations = None
    if confirmations is None:
        return VerificationReport(
            Outcome.UNVERIFIABLE,
            "confirmation depth could not be established",
            reports,
            block_height=height,
        )
    if confirmations < MIN_CONFIRMATIONS:
        return VerificationReport(
            Outcome.UNVERIFIABLE,
            f"confirmation depth {confirmations} is below {MIN_CONFIRMATIONS}",
            reports,
            block_height=height,
            confirmations=confirmations,
        )

    # Steps 10-11. nTime is informative; H is the normative temporal value.
    return VerificationReport(
        Outcome.VALID,
        "artifact is bound to a sufficiently confirmed Bitcoin block",
        reports,
        block_height=height,
        reference_wall_clock_projection=selected.header.ntime,
        confirmations=confirmations,
    )
