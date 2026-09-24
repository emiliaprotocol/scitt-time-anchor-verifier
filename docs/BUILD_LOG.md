# Build and verification log

- Repository: `https://github.com/emiliaprotocol/scitt-time-anchor-verifier`
- Candidate version: `0.1.0`, targeting draft revision `-06`.
- Release tag: `v0.1.0-draft-06`; the tag resolves to the immutable publication
  commit.
- Verification date: 2026-09-24
- Python: `Python 3.14.5`
- Test command: `PYTHONWARNINGS=error python3 -m unittest discover -s tests -t . -v`
- Test result: `Ran 26 tests ... OK`
- Build command: `SCITT_DIST_DIR=dist python3 build_backend.py`
- Wheel SHA-256: `82b3bb3b537d47ce6af9ec213e47e68714451081dc627ad71efa861d7be4ac2c`
- Sdist SHA-256: `1ceeb020ce8b951776c20174cbdc138bae042e85f7e91680142c94bee1bb9cfa`
- Fresh-clone command: `git clone https://github.com/emiliaprotocol/scitt-time-anchor-verifier.git <temporary>/repo`, followed by the test and build commands above.
- Fresh-clone result: clean status before execution; `Ran 26 tests ... OK`;
  wheel and sdist hashes exactly matched the values above.

This log is deliberately excluded from the sdist, whose digest it records. It
remains tracked in the repository; all implementation, tests, vectors,
provenance, conformance, and defect documents are included in the sdist.

## Vector evidence

`python3 tools/rebuild_vectors.py sources/draft-fassbender-scitt-time-anchor-06.txt vectors`
produced four 1877-byte proofs with these SHA-256 digests:

```text
2c1ec4cbe4779d8d598b0f9b951d8d2b351b85ab1d9ad4fe0f897f0b8dd7fd97  vector-1.ots
dc630f6039890b988b2de9c51cf5b93915a24488ab69f05b3d3ed4957febb900  vector-2.ots
4e2a3ce0758ab8bef4b1e8311dea6e987b23a718d6eb40b6ed9f239e8cfe1f73  vector-3.ots
4905b48a6d26ed43a12e92c6a75930b2d36ace7889a5937c61de45f6753b450d  vector-4.ots
```

Every proof parsed to one Bitcoin branch at height 957289, replayed 82
operations, and produced the internal-order header Merkle root
`81383c9ce0d3174bcc6c352a0a821f9e5151e0bc608322ace6aeecccff3c43ef`.
