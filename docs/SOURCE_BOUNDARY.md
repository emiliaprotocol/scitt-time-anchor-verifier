# Clean-room source boundary and provenance log

## Boundary

Only the two technical sources below were admitted. No EMILIA repository,
draft, test, email, memory, artifact, implementation, convention, or prior
clean-room package was inspected or reused. No author or other person was
contacted. The independent implementation URL mentioned in Appendix C was not
opened.

Standard-library behavior and the Python language/runtime were implementation
tools, not protocol sources. The public Bitcoin chain was not queried; test
headers are explicitly synthetic and exercise the caller-owned validated-chain
interface.

## Source 1: published Internet-Draft

- URI: `https://www.ietf.org/archive/id/draft-fassbender-scitt-time-anchor-06.txt`
- Retrieved: 2026-09-24
- Bytes: 225377
- Lines: 5096
- SHA-256: `ff9cc5d7e4221dd53324df02a05565ffb6a55a0502a94acfa412836c8c9103b8`
- Scope used: normative terminology, proof bundle, all eleven verification
  steps, result semantics, batch construction, v0.4.5 pin, and Appendix D
  vectors.

Acquisition command:

```sh
curl -fL --proto '=https' --tlsv1.2 \
  -o sources/draft-fassbender-scitt-time-anchor-06.txt \
  https://www.ietf.org/archive/id/draft-fassbender-scitt-time-anchor-06.txt
shasum -a 256 sources/draft-fassbender-scitt-time-anchor-06.txt
```

## Source 2: pinned OpenTimestamps v0.4.5 source distribution

- Release URI: `https://files.pythonhosted.org/packages/source/o/opentimestamps/opentimestamps-0.4.5.tar.gz`
- Release page named by the draft:
  `https://github.com/opentimestamps/python-opentimestamps/tree/python-opentimestamps-v0.4.5`
- Retrieved: 2026-09-24
- Bytes: 35554
- SHA-256: `56726ccde97fb67f336a7f237ce36808e5593c3089d68d900b1c83d0ebf9dcfa`
- Commit pinned by the draft and verified as the peeled tag target:
  `a90094e3ca9a8229abd016be8816d7b90b9fd1e6`
- Annotated tag object observed:
  `4becfab114dabf9fe70aeefe38808f04c62471a8`
- Software Heritage revision named by the draft:
  `swh:1:rev:a90094e3ca9a8229abd016be8816d7b90b9fd1e6`

Tag verification command and result:

```text
$ git ls-remote https://github.com/opentimestamps/python-opentimestamps.git 'refs/tags/python-opentimestamps-v0.4.5*'
4becfab114dabf9fe70aeefe38808f04c62471a8 refs/tags/python-opentimestamps-v0.4.5
a90094e3ca9a8229abd016be8816d7b90b9fd1e6 refs/tags/python-opentimestamps-v0.4.5^{}
```

Files consulted inside the verified source distribution:

| File | SHA-256 |
|---|---|
| `setup.py` | `d2bcb6c460b47e596317b09a14d592caa52222d937c6add09cfa42d4876cd472` |
| `README.md` | `297044a0959f664b052d160247e2a9f193f6d5453185c6295f99d9f29b810e87` |
| `opentimestamps/core/serialize.py` | `eb3a1292e212e855fa378204872f7b04ce03a998abae1b4699c0f29e1492d29a` |
| `opentimestamps/core/timestamp.py` | `b1508e36270748399fa8a88b5dc7b895351cec91fea7b0c7b66f6e3f4b82a2e6` |
| `opentimestamps/core/op.py` | `a1159335fa7c558c93c6ff1dd40c872bcc8e0872d4de1a07f0ca23ed5719cf4b` |
| `opentimestamps/core/notary.py` | `2d39368c0d3f12a7ecbc731752a6edb7ec8548087eecd5cb3f7bfaa5da4646a1` |
| `opentimestamps/core/dubious/notary.py` | `0a7fccfd6eca0bf6a07dbdf41c2341ac8b395d808bb349d85c3f7e8f9e754fab` |
| `opentimestamps/tests/core/test_serialize.py` | `b8be25230d429550a180cb7de2c43b895102279aa6bff36c29f29a3f119680ad` |
| `opentimestamps/tests/core/test_timestamp.py` | `5cee393130858549942ab05ad35c0589ac153ca90c9982796d179b09f510af0e` |

## Derived material

The four `vectors/vector-*.ots` files are decoded mechanically from Appendix
D.5 by `tools/rebuild_vectors.py`. Their committed SHA-256 values exactly match
the values printed in the draft. `vectors/manifest.json` transcribes the
artifacts, nonces, leaves, intermediate nodes, root, height, Merkle root, and
informative block time printed in Appendix D.

Neither downloaded source archive is committed. `tools/fetch_sources.py`
reconstructs the source inputs and refuses a hash mismatch.
