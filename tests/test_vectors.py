from __future__ import annotations

import hashlib
import json
import pathlib
import unittest

from scitt_time_anchor import Outcome, ProofBundle, build_batch_paths, verify_anchor
from scitt_time_anchor.ots import parse_detached_timestamp

from ._support import MemoryHeaderSource, header


ROOT = pathlib.Path(__file__).resolve().parents[1]


class AppendixDVectorsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "vectors" / "manifest.json").read_text())

    def test_batch_construction_reproduces_every_printed_value(self):
        vectors = self.manifest["vectors"]
        result = build_batch_paths(
            [item["artifact_sha256"] for item in vectors],
            nonces=[bytes.fromhex(item["nonce"]) for item in vectors],
        )
        self.assertEqual(result.merkle_root.hex(), self.manifest["batch_root"])
        for actual, expected in zip(result.paths, vectors, strict=True):
            self.assertEqual(actual.leaf.hex(), expected["leaf"])

        # Appendix D.2's two first-level nodes.
        node_12 = hashlib.sha256(result.paths[0].leaf + result.paths[1].leaf).hexdigest()
        node_34 = hashlib.sha256(result.paths[2].leaf + result.paths[3].leaf).hexdigest()
        self.assertEqual(node_12, self.manifest["node_12"])
        self.assertEqual(node_34, self.manifest["node_34"])

    def test_all_four_proofs_parse_replay_and_verify(self):
        merkle_root = bytes.fromhex(self.manifest["header_merkle_root_internal"])
        height_value = self.manifest["block_height"]
        for item in self.manifest["vectors"]:
            with self.subTest(vector=item["number"]):
                proof = (ROOT / "vectors" / item["proof"]).read_bytes()
                artifact = item["artifact"].encode("ascii")
                self.assertEqual(hashlib.sha256(proof).hexdigest(), item["proof_sha256"])
                self.assertEqual(hashlib.sha256(artifact).hexdigest(), item["artifact_sha256"])
                parsed = parse_detached_timestamp(proof)
                self.assertEqual(parsed.message.hex(), item["artifact_sha256"])
                self.assertEqual(len(parsed.bitcoin_branches), 1)
                branch = parsed.bitcoin_branches[0]
                self.assertEqual(branch.height, height_value)
                self.assertEqual(len(branch.operations), 82)
                self.assertEqual(branch.replay_sha256_profile(parsed.message), merkle_root)

                source = MemoryHeaderSource(
                    {height_value: header(merkle_root)}, confirmations=6
                )
                report = verify_anchor(
                    artifact,
                    ProofBundle(
                        proof,
                        "sha256:" + item["artifact_sha256"],
                        origin_id="ignored",
                        bitcoin_block_height=0,
                    ),
                    source,
                )
                self.assertEqual(report.outcome, Outcome.VALID)
                self.assertEqual(report.block_height, height_value)
                self.assertEqual(report.confirmations, 6)
                self.assertEqual(
                    report.reference_wall_clock_projection,
                    self.manifest["reference_wall_clock_projection"],
                )

    def test_appendix_d_negative_vector_is_invalid(self):
        item = self.manifest["vectors"][0]
        proof = (ROOT / "vectors" / item["proof"]).read_bytes()
        source = MemoryHeaderSource()
        report = verify_anchor(
            (item["artifact"] + "!").encode("ascii"),
            ProofBundle(proof, item["artifact_sha256"]),
            source,
        )
        self.assertEqual(report.outcome, Outcome.INVALID)
        self.assertEqual(source.header_calls, [])


if __name__ == "__main__":
    unittest.main()
