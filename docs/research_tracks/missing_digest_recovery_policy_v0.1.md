# Missing Digest Recovery Policy v0.1

## Trigger

Use this policy when a public daily date lacks either `digests/YYYY-MM-DD.md` or `data/YYYY-MM-DD.json`.

## Recovery Procedure

1. Confirm the date is genuinely missing.
2. Run environment imports and workflow doctor.
3. Run an explicit date-targeted command with `--date YYYY-MM-DD`.
4. Use `--retry-failed-sources` and `--include-latest-sources` only as deliberate manual recovery flags.
5. Confirm both artifacts exist and contain the requested target date and coverage window.
6. Record source-health degradation and source-starved status.
7. Regenerate dependent handoff output when appropriate.
8. Run project tests and release hygiene.

## Decision Rules

- Nonzero records with degraded source health: accept the artifact, retain warnings, and schedule no automatic retry.
- Zero records with healthy sources: valid empty digest, subject to content review.
- Zero records with all-red sources: source-starved artifact; manual recovery remains required.
- Existing authoritative artifact: do not overwrite casually; use the established backfill/force policy.

## Boundaries

- Recovery is manual-only.
- Recovery does not alter ranking or source semantics.
- Recovery does not imply that generated artifacts should be committed.
- Recovery never writes to private application or separate ResearchArtifacts workspaces.

