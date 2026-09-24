from __future__ import annotations

import hashlib
import unittest

from scitt_time_anchor import build_batch_paths


class BatchConstructionTest(unittest.TestCase):
    def test_pair_and_promote_for_odd_count(self):
        hashes = [hashlib.sha256(bytes((value,))).hexdigest() for value in range(3)]
        nonces = [bytes((value,)) * 16 for value in range(3)]
        result = build_batch_paths(hashes, nonces=nonces)
        leaves = [hashlib.sha256(bytes.fromhex(value) + nonce).digest() for value, nonce in zip(hashes, nonces)]
        first_pair = hashlib.sha256(leaves[0] + leaves[1]).digest()
        expected = hashlib.sha256(first_pair + leaves[2]).digest()
        self.assertEqual(result.merkle_root, expected)
        self.assertEqual(len(result.paths[0].operations), 6)
        self.assertEqual(len(result.paths[2].operations), 4)

    def test_rejects_empty_batch(self):
        with self.assertRaises(ValueError):
            build_batch_paths([])

    def test_rejects_uppercase_hash(self):
        with self.assertRaises(ValueError):
            build_batch_paths(["AA" * 32], nonces=[bytes(16)])

    def test_rejects_bad_nonce_size(self):
        with self.assertRaises(ValueError):
            build_batch_paths(["00" * 32], nonces=[bytes(15)])


if __name__ == "__main__":
    unittest.main()
