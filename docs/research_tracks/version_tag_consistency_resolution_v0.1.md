# Version-Tag Consistency Resolution v0.1

## Decision

`prepare_v0_4_1`

## Historical State

- immutable tag: `v0.4.0`;
- target: `08c5f07967739ecd008773c4b167cd736848df88`;
- timestamp: `2026-06-11T01:05:06+08:00`;
- package metadata at target: `0.3.3`.

## Resolution

Active version sources are aligned to `0.4.1`:

- `pyproject.toml`;
- `src/lattice_digest/__init__.py`;
- root bridge `lattice_digest/__init__.py`.

The existing tag is not moved, deleted, recreated, or reinterpreted. A new tag is not created in Phase 12Z.
