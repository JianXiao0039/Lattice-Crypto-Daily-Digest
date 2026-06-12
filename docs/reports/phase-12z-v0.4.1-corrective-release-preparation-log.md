# Phase 12Z: v0.4.1 Corrective Release Preparation Log

## Decision

`prepare_v0_4_1`

## Version Sources

| Source | Before | Prepared value |
|---|---:|---:|
| `pyproject.toml` | 0.3.3 | 0.4.1 |
| `src/lattice_digest/__init__.py` | 0.3.3 | 0.4.1 |
| `lattice_digest/__init__.py` | 0.3.3 | 0.4.1 |

## Documentation

- Added `docs/releases/v0.4.1.md`.
- Added a changelog entry.
- Updated README and docs index.
- Preserved v0.3.3 and v0.4.0 historical records.

## Tests

- Updated active release assertions.
- Converted v0.3.3 current-version assertions to archival assertions.
- Added `tests/test_release_v041_docs.py`.

## Release State

No tag was created. Full tests pass with 464 tests. `git diff --check` passes.

Explicit release hygiene remains blocked because `papers.db` was already staged in the working index. Phase 12Z did not alter that staging state. Final release readiness also requires a Windows CI rerun and durable Daily submission evidence.
