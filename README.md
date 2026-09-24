# SCITT time-anchor -06 clean-room verifier

This repository is an independent, zero-runtime-dependency Python
implementation of the verifier specified by
`draft-fassbender-scitt-time-anchor-06`, using the serialized proof grammar and
operation semantics pinned to `python-opentimestamps` v0.4.5.

The implementation includes:

- the exact three-result `VERIFY-ANCHOR` procedure (`valid`, `invalid`, or
  `unverifiable`);
- a standalone parser for v0.4.5 detached `.ots` proofs;
- per-branch append/prepend/SHA-256 replay, without calling OpenTimestamps;
- the mandatory six-confirmation gate;
- Section 4.3 blinded pair-and-promote batch-path construction; and
- all four Appendix D proofs, reconstructed from the published draft and
  checked against their printed SHA-256 digests.

It deliberately does **not** treat a block explorer response as validated
Bitcoin state. The caller must supply a `ValidatedHeaderSource` that has placed
each returned header on the independently validated most-work chain and derives
confirmation depth from that same chain. This semantic boundary is required by
Sections 3.1 and 3.2. The library cannot establish it from an 80-byte header
alone.

## Minimal use

```python
from scitt_time_anchor import ProofBundle, verify_anchor

# `node_headers` is owned by the verifier and implements
# ValidatedHeaderSource. It must not be the anchoring service or a facade over
# an unvalidated explorer response.
report = verify_anchor(
    artifact_bytes,
    ProofBundle(ots_proof=proof_bytes, claimed_hash="sha256:" + digest_hex),
    node_headers,
)

print(report.outcome.value)
print(report.block_height)  # normative temporal value when established
print(report.reference_wall_clock_projection)  # miner-set, informative only
```

`origin_id` and the ProofBundle's cached `bitcoin_block_height` are accepted
and ignored as the draft requires.

## Verify and build

```sh
python3 -m unittest discover -s tests -t . -v
python3 build_backend.py
shasum -a 256 dist/*
```

The custom PEP 517 backend uses only the Python standard library and normalizes
archive order, metadata, ownership, modes, and timestamps. Repeating the build
from the same commit produces byte-identical wheel and source archives.

See [REPRODUCING.md](REPRODUCING.md) for fresh-checkout commands,
[docs/SOURCE_BOUNDARY.md](docs/SOURCE_BOUNDARY.md) for provenance,
[docs/CONFORMANCE.md](docs/CONFORMANCE.md) for the requirement map, and
[docs/AMBIGUITIES.md](docs/AMBIGUITIES.md) for the defect record.

## Scope and claim

This is a verifier-core implementation, not a Bitcoin consensus implementation
or an anchoring service. It does not submit to calendars, upgrade pending
proofs, validate Bitcoin consensus, select the most-work chain, or issue SCITT
receipts. A deployment can claim a conformant `valid` result only when its
`ValidatedHeaderSource` really satisfies the draft's independent-chain
requirements.

The bundled tests use a synthetic source to exercise the algorithm. They prove
parser, replay, branching, result-classification, confirmation-gate, vector,
and build behavior. They do not constitute a live full-node verification of
Bitcoin block 957289.

## Project identity

This independent clean-room implementation is published by Iman Schrock for
the EMILIA Protocol project. No draft author or other person was consulted
during the implementation. Publication does not imply endorsement by a draft
author, the IETF, SCITT, Bitcoin, or OpenTimestamps.

The software is MIT licensed. The pinned Internet-Draft remains a work in
progress and can be replaced or expire; this release intentionally targets
revision `-06`, not a moving document.
