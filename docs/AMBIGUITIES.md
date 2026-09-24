# Defect and ambiguity record

No author was asked to resolve these points. Each encountered ambiguity is
treated as a specification defect and the implementation's bounded behavior is
recorded here.

## D-01: the OTS Bitcoin tag does not encode a Bitcoin network

Table 1 requires F4 `ledger_id` and gives `bitcoin-mainnet` as an example.
Table 4 maps F4 only to the Bitcoin attestation tag. The v0.4.5 tag identifies
Bitcoin but contains only a height and does not distinguish mainnet, testnet,
signet, or another header chain.

**Implementation:** the proof parser reports a Bitcoin attestation; network and
validated-chain identity belong to the caller's `ValidatedHeaderSource`. The
library does not claim to recover `bitcoin-mainnet` from proof bytes.

## D-02: alternative serialization is permitted but cannot be negotiated

Section 2.4.2 permits an alternative serialization carrying the required
abstract fields. Section 3.1 step 3 unconditionally invokes OTS-DESERIALIZE on
the opaque `ots_proof` member, and the ProofBundle has no format identifier.

**Implementation:** only the explicitly pinned v0.4.5 OTS serialization is
accepted. No alternative format is guessed.

## D-03: F7 `tx_id` has no normative boundary marker

Table 1 says `tx_id` SHOULD be carried; Table 4 says it is encoded in proof
operations and recoverable. An OTS path is an untyped operation sequence after
deserialization. It can pass through transaction bytes, but it does not mark
which prepend/append/hash subsequence is the transaction boundary. Appendix D
identifies the boundary for those particular proofs, not for arbitrary proofs.

**Implementation:** verification does not need or extract F7. Generic F7
recovery is not claimed.

## D-04: F9 is both outside the proof and described as implicit in it

Section 2.4.1 says F9 is recorded by the producer and is not part of any proof.
Table 4 then maps presence of a Bitcoin attestation to `anchored`, while nearby
text adds a confirmation-depth condition that proof bytes cannot record.

**Implementation:** producer status is ignored. Presence of an attestation,
header match, and confirmation depth are evaluated independently.

## D-05: claimed-hash hexadecimal case is not stated in the field definition

The terminology calls `claimed_hash` a hex string, while `HEX` is explicitly
lowercase, step 2 uses direct string comparison, and Section 4.3's regex accepts
only `[0-9a-f]`.

**Implementation:** lowercase is required. Uppercase or mixed-case claims are
`invalid` under the literal algorithm.

## D-06: VERIFY-ANCHOR does not explicitly check required F2

F2 MUST be `sha256` and Table 4 maps it to initial operation byte `0x08`.
Step 3 checks only parse success and message equality. A different 32-byte OTS
file-hash operation could therefore carry bytes equal to the artifact's SHA-256
while violating F2.

**Implementation:** step 3 also requires the initial operation to be `0x08`.
This enforces the abstract-field MUST rather than accepting the algorithmic
omission.

## D-07: an empty batch has no defined result

Section 4.3 validates each input and later reads `level[0]`; it never states a
minimum batch size.

**Implementation:** an empty input raises `ValueError`. A one-origin batch is
accepted and its blinded leaf is the root.

## D-08: validation of a header source is a semantic, not type-level, property

The draft correctly rejects a merely reported header but defines an abstract
fetch operation rather than a concrete validation API. An 80-byte header does
not prove how it was obtained or whether it belongs to the most-work chain.

**Implementation:** `ValidatedHeaderSource` is an explicit caller contract. No
explorer adapter is supplied and tests label their source synthetic. A caller
that violates the contract cannot claim a conformant `valid` result.

## D-09: Table 5's `unverifiable` row is not exhaustive

The algorithm also returns `unverifiable` when a branch uses an operation
outside the profile, or when confirmation depth cannot be established. Table 5
lists neither condition in its compact row, though the surrounding normative
algorithm does.

**Implementation:** the algorithm controls: both conditions return
`unverifiable`.

## D-10: `claimed_hash` is called non-authoritative but is failure-bearing

Sections 1.3 and 2.4.3 say the verifier must not treat `claimed_hash` as
authoritative. Step 2 nevertheless makes a mismatch independently sufficient
for `invalid`, even if the proof message would match the recomputed artifact
hash.

**Implementation:** the field is not trusted as the artifact digest, but the
required comparison is performed and can return `invalid` exactly as written.

## D-11: malformed behavior from the abstract header source is unspecified

FETCH-BLOCK-HEADER-BY-HEIGHT is specified to return an 80-byte header or NULL.
The draft does not classify an exception, a wrong-length value, or a non-header
object from an integration boundary.

**Implementation:** exceptions and non-`BlockHeader` values are treated as no
established header and therefore as `unavailable`/`unverifiable`.

## D-12: direct-construction output shape is inconsistent

Section 4.1 declares two outputs (`origin_record`, `pending_proof`), but the
shown returns contain only an origin/status object and omit the serialized
proof from the return value.

**Implementation:** direct calendar construction is not exposed. The defect
does not affect the normative verifier.

## D-13: Appendix D vectors retain a `-03` artifact label

Revision -06's four artifact strings identify themselves as revision `-03`.
The hashes and proofs are internally consistent, but the label can be mistaken
for the revision implemented.

**Implementation:** bytes are preserved exactly; manifest provenance says
revision -06 Appendix D and never rewrites the artifact.

## D-14: the pinned source distribution omits its referenced license file

The v0.4.5 source files say their terms are in a top-level `LICENSE`, and
package metadata declares LGPLv3, but the hash-pinned source distribution does
not contain a `LICENSE` member.

**Implementation:** no upstream file is vendored or imported at runtime. The
independent implementation is MIT licensed and records the upstream pin and
consulted-file hashes. This note is provenance, not a legal conclusion.

## D-15: there is no bound on detached-proof or varuint size

The v0.4.5 parser bounds operation arguments, attestation payloads, and
recursion, but not total proof bytes or the byte length of an unsigned LEB128
integer. The draft imports that parser behavior without adding resource bounds.

**Implementation:** compatibility is preserved: no new acceptance-changing
cap is imposed. Callers handling hostile inputs should bound the byte string
before calling the parser. A future profile should specify a proof-size and
integer-encoding limit.

## D-16: confirmation-depth prose has an off-by-one inconsistency

The terminology and step 9 define confirmation depth as the number of blocks
at H and above, counting H itself. Six confirmations therefore require H plus
five later blocks. Section 6.7 instead says a stored set must extend "at least
MIN_CONFIRMATIONS blocks beyond" H, which would require six later blocks and
produce a count of seven under the normative definition.

**Implementation:** the explicit definition and algorithm control. The source
returns an inclusive count, and `valid` requires that count to be at least six.

## D-17: pending proofs contradict the unconditional required-field table

Section 2.4.1 first says a conformant Anchor Proof MUST encode F1 through F5.
It later says a proof recorded as pending needs only F1, F2, and a partial F3.
A pending OTS proof necessarily has no Bitcoin tag or attested height, so it
cannot contain F4/F5 under Table 4's mapping.

**Implementation:** the later pending-proof rule and VERIFY-ANCHOR step 4
control. A syntactically valid calendar-only proof is accepted as pending input
and returns `unverifiable`, not a parse-level `invalid` result.
