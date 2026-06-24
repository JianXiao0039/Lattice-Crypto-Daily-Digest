# Legacy Artifact Path Compatibility v0.1

## Deprecated Legacy Paths

Legacy Markdown paths:

```text
digests\YYYY-MM-DD.md
digests\weekly\YYYY-Www.md
digests\monthly\YYYY-MM.md
```

Legacy JSON/data paths:

```text
data\YYYY-MM-DD.json
data\weekly\YYYY-Www.json
data\monthly\YYYY-MM.json
```

These paths remain read-only fallback locations during the migration window.

## Phase 14S-A Default

Canonical-only lookup is now the default in the uncommitted working tree when
`LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK` is absent.

Temporary compatibility fallback remains available only through explicit opt-in:

```powershell
$env:LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK = "1"
```

Compatibility fallback is read-only, temporary, and observable. It never changes
writer output paths.

## Lookup Order

Readers must use this order:

1. canonical year-partitioned path;
2. legacy path only when canonical is absent and compatibility fallback is explicitly enabled;
3. warning/report entry when legacy fallback is used.

Readers must not silently prefer stale legacy files when canonical files exist.

## Writer Restriction

New writers must not write legacy artifacts. This restriction applies to:

- Daily retrieval/rendering;
- Weekly synthesis;
- Monthly synthesis;
- historical backfill scripts;
- durable verification outputs;
- quality audits and export workflows that write radar artifacts.

## Pruning Policy

Legacy files must not be deleted by normal apply migration. Pruning requires:

- explicit `-PruneLegacy`;
- verified canonical target;
- matching hashes where appropriate;
- no unresolved collision;
- reviewed migration manifest.

## Future Removal Milestone

Legacy fallback can be removed only after:

- migration apply has completed;
- focused path tests pass;
- durable verification passes against canonical paths;
- backfill scripts validate canonical artifacts;
- the user explicitly approves removal of fallback support.

## Phase 14N Status

Phase 14N validated canonical-first operations with limits:

- no legacy writes were detected during canary operations;
- Daily, Weekly, Monthly, durable verification, reading queue, Obsidian export, and weekly handoff checks used canonical paths where available;
- legacy fallback remains enabled and read-only;
- fallback removal is not approved in Phase 14N.

## Phase 14O Status

Phase 14O added canonical-only shadow validation through:

```text
scripts\audit_legacy_fallback_usage.py
```

The Phase 14O diagnostic result for discovered 2025/2026 artifacts was:

- fallback used: `0`;
- deprecation blockers: `0`;
- persisted legacy references: `1`;
- persisted legacy runtime dependencies: `0`;
- decision: `legacy_fallback_ready_with_documented_exceptions`.

Default runtime behavior permitted legacy fallback in Phase 14O. Phase 14S-A
changes the uncommitted working-tree default to canonical-only and preserves
explicit opt-in compatibility mode. No legacy artifact was deleted.
