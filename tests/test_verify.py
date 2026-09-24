from __future__ import annotations

import hashlib
import unittest

from scitt_time_anchor import Outcome, ProofBundle, verify_anchor

from ._support import (
    MemoryHeaderSource,
    bitcoin_attestation,
    detached,
    digest_path,
    header,
    pending_attestation,
    varbytes,
)


class VerifyAnchorTest(unittest.TestCase):
    def setUp(self):
        self.artifact = b"clean-room artifact"
        self.message = hashlib.sha256(self.artifact).digest()
        self.claim = "sha256:" + self.message.hex()

    def _single_branch_proof(self, suffix=b"x", height_value=50):
        timestamp = b"\xf0" + varbytes(suffix) + b"\x08" + bitcoin_attestation(height_value)
        root = digest_path(self.message, suffix)
        return detached(self.message, timestamp), height_value, root

    def test_pending_proof_is_unverifiable(self):
        proof = detached(self.message, pending_attestation("https://calendar.example"))
        report = verify_anchor(
            self.artifact, ProofBundle(proof, self.claim), MemoryHeaderSource()
        )
        self.assertEqual(report.outcome, Outcome.UNVERIFIABLE)
        self.assertIn("no Bitcoin", report.reason)

    def test_fewer_than_six_confirmations_is_unverifiable(self):
        proof, height_value, root = self._single_branch_proof()
        report = verify_anchor(
            self.artifact,
            ProofBundle(proof, self.claim),
            MemoryHeaderSource({height_value: header(root)}, confirmations=5),
        )
        self.assertEqual(report.outcome, Outcome.UNVERIFIABLE)
        self.assertEqual(report.confirmations, 5)

    def test_unknown_confirmation_depth_is_unverifiable(self):
        proof, height_value, root = self._single_branch_proof()
        report = verify_anchor(
            self.artifact,
            ProofBundle(proof, self.claim),
            MemoryHeaderSource({height_value: header(root)}, confirmations=None),
        )
        self.assertEqual(report.outcome, Outcome.UNVERIFIABLE)

    def test_missing_header_is_unverifiable(self):
        proof, _, _ = self._single_branch_proof()
        report = verify_anchor(
            self.artifact, ProofBundle(proof, self.claim), MemoryHeaderSource()
        )
        self.assertEqual(report.outcome, Outcome.UNVERIFIABLE)
        self.assertEqual(report.branches[0].state, "unavailable")

    def test_mismatched_header_is_invalid(self):
        proof, height_value, _ = self._single_branch_proof()
        report = verify_anchor(
            self.artifact,
            ProofBundle(proof, self.claim),
            MemoryHeaderSource({height_value: header(bytes(32))}),
        )
        self.assertEqual(report.outcome, Outcome.INVALID)
        self.assertEqual(report.branches[0].state, "mismatched")

    def test_unsupported_branch_is_unverifiable(self):
        # sha1 is legal in v0.4.5 but outside the profile replay subset.
        proof = detached(self.message, b"\x02" + bitcoin_attestation(50))
        report = verify_anchor(
            self.artifact,
            ProofBundle(proof, self.claim),
            MemoryHeaderSource({50: header(bytes(32))}),
        )
        self.assertEqual(report.outcome, Outcome.UNVERIFIABLE)
        self.assertEqual(report.branches[0].state, "unsupported")

    def test_multiple_branches_select_lowest_verified_height(self):
        suffix_high = b"high"
        suffix_low = b"low"
        first = (
            b"\xf0"
            + varbytes(suffix_high)
            + b"\x08"
            + bitcoin_attestation(100)
        )
        second = (
            b"\xf0"
            + varbytes(suffix_low)
            + b"\x08"
            + bitcoin_attestation(90)
        )
        proof = detached(self.message, b"\xff" + first + second)
        source = MemoryHeaderSource(
            {
                100: header(digest_path(self.message, suffix_high)),
                90: header(digest_path(self.message, suffix_low)),
            },
            confirmations={90: 20, 100: 10},
        )
        report = verify_anchor(self.artifact, ProofBundle(proof, self.claim), source)
        self.assertEqual(report.outcome, Outcome.VALID)
        self.assertEqual(report.block_height, 90)
        self.assertEqual(source.confirmation_calls, [90])

    def test_one_verified_branch_suffices(self):
        suffix_good = b"good"
        suffix_bad = b"bad"
        first = b"\xf0" + varbytes(suffix_bad) + b"\x08" + bitcoin_attestation(40)
        second = b"\xf0" + varbytes(suffix_good) + b"\x08" + bitcoin_attestation(41)
        proof = detached(self.message, b"\xff" + first + second)
        source = MemoryHeaderSource(
            {
                40: header(bytes(32)),
                41: header(digest_path(self.message, suffix_good)),
            }
        )
        report = verify_anchor(self.artifact, ProofBundle(proof, self.claim), source)
        self.assertEqual(report.outcome, Outcome.VALID)
        self.assertEqual([branch.state for branch in report.branches], ["mismatched", "verified"])

    def test_mismatch_plus_unavailable_is_unverifiable(self):
        first = b"\xf0" + varbytes(b"a") + b"\x08" + bitcoin_attestation(40)
        second = b"\xf0" + varbytes(b"b") + b"\x08" + bitcoin_attestation(41)
        proof = detached(self.message, b"\xff" + first + second)
        source = MemoryHeaderSource({40: header(bytes(32))})
        report = verify_anchor(self.artifact, ProofBundle(proof, self.claim), source)
        self.assertEqual(report.outcome, Outcome.UNVERIFIABLE)

    def test_claim_comparison_is_exact_lowercase(self):
        proof, height_value, root = self._single_branch_proof()
        report = verify_anchor(
            self.artifact,
            ProofBundle(proof, self.message.hex().upper()),
            MemoryHeaderSource({height_value: header(root)}),
        )
        self.assertEqual(report.outcome, Outcome.INVALID)

    def test_non_sha256_initial_hash_operation_is_invalid(self):
        # Keccak has the same digest length, making the F2 check observable.
        proof = detached(self.message, bitcoin_attestation(1), hash_tag=0x67)
        report = verify_anchor(
            self.artifact, ProofBundle(proof, self.claim), MemoryHeaderSource()
        )
        self.assertEqual(report.outcome, Outcome.INVALID)
        self.assertIn("not sha256", report.reason)


if __name__ == "__main__":
    unittest.main()
