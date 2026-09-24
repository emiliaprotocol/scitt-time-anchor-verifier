from __future__ import annotations

import hashlib
import unittest

from scitt_time_anchor.ots import HEADER_MAGIC, OTSParseError, parse_detached_timestamp

from ._support import bitcoin_attestation, detached, pending_attestation


class OTSParserTest(unittest.TestCase):
    def setUp(self):
        self.message = hashlib.sha256(b"parser").digest()

    def test_rejects_bad_magic(self):
        with self.assertRaises(OTSParseError):
            parse_detached_timestamp(b"not a proof")

    def test_rejects_trailing_garbage(self):
        proof = detached(self.message, bitcoin_attestation(1)) + b"garbage"
        with self.assertRaises(OTSParseError):
            parse_detached_timestamp(proof)

    def test_rejects_unknown_major_version(self):
        proof = HEADER_MAGIC + b"\x02\x08" + self.message + bitcoin_attestation(1)
        with self.assertRaises(OTSParseError):
            parse_detached_timestamp(proof)

    def test_rejects_unknown_operation(self):
        proof = detached(self.message, b"\x42" + bitcoin_attestation(1))
        with self.assertRaises(OTSParseError):
            parse_detached_timestamp(proof)

    def test_rejects_invalid_pending_uri(self):
        # Query markers are forbidden by v0.4.5's URI character set.
        proof = detached(self.message, pending_attestation("https://x.invalid/?q=1"))
        with self.assertRaises(OTSParseError):
            parse_detached_timestamp(proof)

    def test_accepts_nonminimal_varuint_like_v045(self):
        # Version 1 encoded non-minimally as 0x81 0x00.
        proof = (
            HEADER_MAGIC
            + b"\x81\x00\x08"
            + self.message
            + bitcoin_attestation(1)
        )
        parsed = parse_detached_timestamp(proof)
        self.assertEqual(parsed.message, self.message)

    def test_enforces_timestamp_recursion_limit(self):
        proof = detached(self.message, b"\x08" * 256 + bitcoin_attestation(1))
        with self.assertRaises(OTSParseError):
            parse_detached_timestamp(proof)


if __name__ == "__main__":
    unittest.main()
