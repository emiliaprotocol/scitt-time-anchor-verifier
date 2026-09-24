# Publication candidate statement

## Publisher identity wording

Use wording no stronger than:

> This independent clean-room implementation is published by Iman Schrock for
> the EMILIA Protocol project. No draft author or other person was consulted.
> The implementation used only the published revision -06 draft and the
> hash-pinned OpenTimestamps v0.4.5 source identified in the provenance log.

Do not describe the implementation as endorsed by the draft author, IETF,
SCITT, Bitcoin, or OpenTimestamps.

## Candidate boundary

The commit identified in `docs/BUILD_LOG.md` is suitable for commit-pinned
technical publication as an independent verifier-core candidate if the
publication preserves:

1. the publisher identity statement above;
2. the source boundary and exact hashes;
3. the defect record;
4. the distinction between synthetic algorithm tests and live full-node
   verification; and
5. the statement that the Internet-Draft is work in progress.

It is not evidence that a live deployment has independently validated Bitcoin
block 957289. Publication must not turn the caller contract
`ValidatedHeaderSource` into an assertion that a particular integration meets
it.
