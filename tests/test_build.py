from __future__ import annotations

import hashlib
import pathlib
import tarfile
import tempfile
import unittest
import zipfile

import build_backend


class ReproducibleBuildTest(unittest.TestCase):
    def test_wheel_and_sdist_are_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_wheel = pathlib.Path(first) / build_backend.build_wheel(first)
            second_wheel = pathlib.Path(second) / build_backend.build_wheel(second)
            first_sdist = pathlib.Path(first) / build_backend.build_sdist(first)
            second_sdist = pathlib.Path(second) / build_backend.build_sdist(second)
            self.assertEqual(
                hashlib.sha256(first_wheel.read_bytes()).digest(),
                hashlib.sha256(second_wheel.read_bytes()).digest(),
            )
            self.assertEqual(
                hashlib.sha256(first_sdist.read_bytes()).digest(),
                hashlib.sha256(second_sdist.read_bytes()).digest(),
            )
            with zipfile.ZipFile(first_wheel) as archive:
                self.assertTrue(any(name.endswith("/RECORD") for name in archive.namelist()))
                self.assertTrue(any(name.endswith("/licenses/NOTICE") for name in archive.namelist()))
                self.assertFalse(any(name.startswith("sources/") for name in archive.namelist()))
            with tarfile.open(first_sdist, "r:gz") as archive:
                self.assertIn(
                    "scitt-time-anchor-cleanroom-0.1.0/PKG-INFO",
                    archive.getnames(),
                )
                self.assertIn(
                    "scitt-time-anchor-cleanroom-0.1.0/NOTICE",
                    archive.getnames(),
                )


if __name__ == "__main__":
    unittest.main()
