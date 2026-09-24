# Conformance map

The claim here is bounded: the package implements the revision -06 verifier
core and the draft's deterministic batch-path construction. A deployment's
claim to `valid` additionally depends on its `ValidatedHeaderSource` meeting the
independent-chain contract.

| Draft requirement | Implementation/evidence |
|---|---|
| 2.4.3 ProofBundle | `model.ProofBundle`; required proof and claimed hash, optional metadata accepted |
| 3.1 step 1 | SHA-256 recomputation in `verify_anchor` |
| 3.1 step 2 | exact lowercase `HEX` and exact optional `sha256:` stripping |
| 3.1 step 3 | standalone v0.4.5 parser; initial message and required SHA-256 operation checked |
| 3.1 step 4 | no Bitcoin branch returns `unverifiable` |
| 3.1 steps 5-6 | every Bitcoin branch keeps its own operations and attested height |
| 3.1 step 7 | caller-owned `ValidatedHeaderSource`, cached only by height |
| 3.1 step 8 | unsupported/unavailable/verified/mismatched classification and specified combination rule |
| 3.1 step 8 selection | lowest verified height selected |
| 3.1 step 9 | fixed `MIN_CONFIRMATIONS = 6`; unknown or shallow depth is `unverifiable` |
| 3.1 steps 10-11 | height returned as normative value; nTime separately named informative projection |
| 3.2 independence | no calendar, anchoring service, CA, account, or API dependency in verifier |
| 3.3 result set | closed `Outcome` enum with exactly three values; reason is diagnostic only |
| 4.3 steps 1-3 | lowercase input validation, 16-byte nonce blinding, sequential pair-and-promote paths |
| 6.2.1 format pin | parser tags, limits, grammar, duplicate behavior, and recursion limit taken from verified v0.4.5 source |
| Appendix D | four proof hashes, messages, 82-op replays, height, header-root result, construction values, and negative artifact test |

## Intentionally not claimed

- Calendar HTTP submission and `OTS-UPGRADE`.
- A producing-service database, scheduler, or producer-status state machine.
- Bitcoin consensus, proof-of-work, difficulty, checkpoint, or most-work-chain
  validation. That is the implementation behind `ValidatedHeaderSource`.
- A block-explorer adapter. An unvalidated explorer response cannot produce
  `valid` under the draft.
- SCITT Signed Statement serialization, Receipt validation, or service metadata.
- Median Time Past calculation.
- Alternative proof serialization. Revision -06 supplies no dispatch or media
  type for one; see defect D-02.
- Extraction of F7 `tx_id`; the OTS path has no normative transaction-boundary
  marker; see defect D-03.

## Evidence limits

The test suite independently parses and replays the four published proofs to
the Merkle root printed in Appendix D. A synthetic source then exercises steps
7-11 and the six-confirmation gate. Because no independently validating Bitcoin
node was available inside the two-source clean-room boundary, this construction
record does not claim a live most-work-chain verification of block 957289.
