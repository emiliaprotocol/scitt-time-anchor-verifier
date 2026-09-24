#!/usr/bin/env python3
"""Fetch and hash the only two technical sources admitted by the clean room."""

from __future__ import annotations

import hashlib
import pathlib
import sys
import urllib.request


SOURCES = (
    (
        "draft-fassbender-scitt-time-anchor-06.txt",
        "https://www.ietf.org/archive/id/draft-fassbender-scitt-time-anchor-06.txt",
        "ff9cc5d7e4221dd53324df02a05565ffb6a55a0502a94acfa412836c8c9103b8",
    ),
    (
        "opentimestamps-0.4.5.tar.gz",
        "https://files.pythonhosted.org/packages/source/o/opentimestamps/"
        "opentimestamps-0.4.5.tar.gz",
        "56726ccde97fb67f336a7f237ce36808e5593c3089d68d900b1c83d0ebf9dcfa",
    ),
)


def main() -> int:
    destination = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "sources")
    destination.mkdir(parents=True, exist_ok=True)
    for filename, url, expected in SOURCES:
        target = destination / filename
        request = urllib.request.Request(
            url, headers={"User-Agent": "scitt-time-anchor-cleanroom/0.1.0"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
        actual = hashlib.sha256(payload).hexdigest()
        if actual != expected:
            raise SystemExit(
                f"refusing {filename}: SHA-256 {actual} != expected {expected}"
            )
        target.write_bytes(payload)
        print(f"{actual}  {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
