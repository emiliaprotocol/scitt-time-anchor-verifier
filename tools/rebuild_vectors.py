#!/usr/bin/env python3
"""Reconstruct Appendix D proof files from the pinned draft text."""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import re
import sys


EXPECTED = (
    {
        "number": 1,
        "artifact": "draft-fassbender-scitt-time-anchor-03 vector 1",
        "artifact_sha256": "a183f624efbbda7d6208b9b5a6f9b0c2c95d90382eb209c44a1131954071f30b",
        "nonce": "14ed82e243f4aff3f1794e6754bfae3b",
        "leaf": "aafc3638a4795c8553b974d36c66aee2a7268ede5535a015fbcc73d01a3b8d52",
        "proof_sha256": "2c1ec4cbe4779d8d598b0f9b951d8d2b351b85ab1d9ad4fe0f897f0b8dd7fd97",
    },
    {
        "number": 2,
        "artifact": "draft-fassbender-scitt-time-anchor-03 vector 2",
        "artifact_sha256": "0df073a986e5e5141c96ec32303b8552ded255e4404d0aff996936a846b48cff",
        "nonce": "b0de8a5526115745c2801d65397db556",
        "leaf": "7306ab5d2290e681f11699730c07e11a6b7b0b4babe30349f3c74d37ba100728",
        "proof_sha256": "dc630f6039890b988b2de9c51cf5b93915a24488ab69f05b3d3ed4957febb900",
    },
    {
        "number": 3,
        "artifact": "draft-fassbender-scitt-time-anchor-03 vector 3",
        "artifact_sha256": "d82bf84f17057c0e3d7aa6f249dfc2e80a877b910ce4ce14dc40e653fd5be40b",
        "nonce": "f6518213abf9ba8a92c3cb3bcdb82355",
        "leaf": "d051a6258f904499056f475bfb69eea50a5018bf58144d25121bf5de22fab9dc",
        "proof_sha256": "4e2a3ce0758ab8bef4b1e8311dea6e987b23a718d6eb40b6ed9f239e8cfe1f73",
    },
    {
        "number": 4,
        "artifact": "draft-fassbender-scitt-time-anchor-03 vector 4",
        "artifact_sha256": "94a86d117047f2af9a2f5635d0c530cc85fc23d20f5d4b42926b94abee7a06ec",
        "nonce": "2fb8ccfdfb881b481695a37deeced8e6",
        "leaf": "8864a03154f5dae2ca5f77aab02ad7fa4ab56129dd1fbe2e2eb2615a5208413d",
        "proof_sha256": "4905b48a6d26ed43a12e92c6a75930b2d36ace7889a5937c61de45f6753b450d",
    },
)

VECTOR_MARKER = re.compile(
    r"^   \*Vector ([1-4])\* \(1877 bytes; SHA-256 of the file:\s*$",
    re.MULTILINE,
)
BASE64_LINE = re.compile(r"^   ([A-Za-z0-9+/]{4,}={0,2})$")


def main() -> int:
    draft = pathlib.Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "sources/draft-fassbender-scitt-time-anchor-06.txt"
    )
    output = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "vectors")
    text = draft.read_text(encoding="utf-8")
    markers = list(VECTOR_MARKER.finditer(text))
    if [int(marker.group(1)) for marker in markers] != [1, 2, 3, 4]:
        raise SystemExit("could not find exactly the four Appendix D vector markers")
    d6 = text.index("D.6.  Negative Test Vector", markers[-1].end())
    output.mkdir(parents=True, exist_ok=True)
    manifest_vectors: list[dict[str, object]] = []
    for index, marker in enumerate(markers):
        expected = EXPECTED[index]
        end = markers[index + 1].start() if index + 1 < len(markers) else d6
        lines = []
        for line in text[marker.end() : end].splitlines():
            match = BASE64_LINE.fullmatch(line)
            if match:
                lines.append(match.group(1))
        payload = base64.b64decode("".join(lines), validate=True)
        actual = hashlib.sha256(payload).hexdigest()
        if len(payload) != 1877 or actual != expected["proof_sha256"]:
            raise SystemExit(
                f"vector {index + 1} failed integrity: {len(payload)} bytes, {actual}"
            )
        filename = f"vector-{index + 1}.ots"
        (output / filename).write_bytes(payload)
        manifest_vectors.append({**expected, "proof": filename, "proof_bytes": 1877})

    manifest = {
        "source": "draft-fassbender-scitt-time-anchor-06 Appendix D",
        "block_height": 957289,
        "header_merkle_root_internal": (
            "81383c9ce0d3174bcc6c352a0a821f9e5151e0bc608322ace6aeecccff3c43ef"
        ),
        "reference_wall_clock_projection": 1783591379,
        "minimum_confirmations": 6,
        "node_12": "034dd422ce07afeb555eb7fdbb93418af23455a9c00b79779c8b02d9217778da",
        "node_34": "7c629aed686c15987a7684fd2e3f12d090447c00cb98568b6b9d99069ba008e3",
        "batch_root": "b4d19ae256a6c3bceb27d1a31fbb3dd3e4574616ebe99a367d6ad7224b7e0749",
        "vectors": manifest_vectors,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for item in manifest_vectors:
        print(f"{item['proof_sha256']}  {output / str(item['proof'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
