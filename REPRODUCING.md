# Reproducing the clean-room result

The committed test vectors make normal verification offline. Source retrieval
is a separate, hash-checked provenance step.

## Fresh-checkout verification

Run from the repository root with Python 3.11 or newer:

```sh
git status --short
python3 -m unittest discover -s tests -t . -v
SCITT_DIST_DIR=dist python3 build_backend.py
shasum -a 256 dist/*
```

The test suite builds the wheel and sdist twice in separate temporary
directories and checks byte equality. No package installation, network access,
calendar contact, anchoring-service contact, API key, or third-party Python
package is needed.

To test the wheel in a disposable environment:

```sh
python3 -m venv /tmp/scitt-time-anchor-wheel-check
/tmp/scitt-time-anchor-wheel-check/bin/python -m pip install --no-deps \
  dist/scitt_time_anchor_cleanroom-0.1.0-py3-none-any.whl
/tmp/scitt-time-anchor-wheel-check/bin/python -c \
  'import scitt_time_anchor; print(scitt_time_anchor.__version__)'
```

## Re-fetch the admitted sources

This operation requires HTTPS and writes only to the ignored `sources/`
directory:

```sh
python3 tools/fetch_sources.py sources
shasum -a 256 sources/draft-fassbender-scitt-time-anchor-06.txt \
  sources/opentimestamps-0.4.5.tar.gz
```

Expected SHA-256 values:

```text
ff9cc5d7e4221dd53324df02a05565ffb6a55a0502a94acfa412836c8c9103b8  draft-fassbender-scitt-time-anchor-06.txt
56726ccde97fb67f336a7f237ce36808e5593c3089d68d900b1c83d0ebf9dcfa  opentimestamps-0.4.5.tar.gz
```

Reconstruct the committed binary vectors from Appendix D:

```sh
python3 tools/rebuild_vectors.py \
  sources/draft-fassbender-scitt-time-anchor-06.txt vectors
git diff --exit-code -- vectors
```

## What a live conformance run additionally needs

A live `valid` result requires an implementation of `ValidatedHeaderSource`
backed by a Bitcoin full/pruned node under the verifier's control, or by a
header-only verifier that has independently checked proof-of-work and selected
the most-work chain from genesis or a verifier-held checkpoint. This repository
does not invent a node adapter from material outside the two admitted sources.
