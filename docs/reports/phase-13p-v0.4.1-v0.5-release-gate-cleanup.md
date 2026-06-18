# Phase 13P v0.4.1 / v0.5 Release Gate Cleanup

## Executive Summary

Phase 13P audits release-gate state without changing tags or running Git write operations.

v0.4.1 decision: `v0_4_1_tag_exists_blocked`.

v0.5 RC decision: `v0_5_rc_ready_with_limits`.

CI decision: `local_tests_green_but_ci_unverified`.

Durable evidence decision: `durable_evidence_ready` for v0.5 representative artifacts; `insufficient_evidence` for v0.4.1 tagged commit durable Daily evidence.

Release notes decision: `release_notes_need_update`.

Production gate: `blocked_until_ci_green`.

## Phase 13O Dependency Status

Phase 13O outputs exist, including:

- `docs/reports/phase-13o-radar-operations-runbook-and-low-load-manual-workflow.md`
- `docs/operations/radar_manual_operations_runbook_v0.1.md`

## Git State

- Current branch: `main`
- HEAD: `e092486203d39913affb1fa8ac97cd3dd03fc513`
- `origin/main`: `e092486203d39913affb1fa8ac97cd3dd03fc513`
- HEAD matches `origin/main`: yes

## v0.4.1 Audit

- Local tag exists: yes
- Remote tag exists: yes
- Local tag object: `52bdda3b491e4717f14e8b40c8a35ff2bc19bad8`
- Peeled target commit: `95215b5afe18b1f13463d03929bfe27f15788695`
- Tag points to HEAD: no
- Tag points to `origin/main`: no
- Package version at tagged commit: `0.4.1`
- Durable Daily artifacts at tagged commit: missing
- Durable evidence manifest at tagged commit: missing
- CI status for tag: unverified locally; current manifest records prior failing CI for the related gate.
- Release note status: stale.

Recommended action: keep v0.4.1 untouched and document it as a blocked historical corrective tag.

## v0.5 RC Audit

v0.5 RC feature set is present for review:

- recommendation rationale;
- bilingual rationale policy for top papers;
- Daily artifacts;
- Weekly artifacts;
- Monthly artifacts;
- source-health diagnostics;
- durable artifact verification;
- reading queue export;
- Obsidian export;
- operations runbooks;
- no manual annotation dependency;
- no background automation;
- no anti-bot bypass.

## Durable Evidence

Representative target period:

- Daily: `2026-06-15`
- Weekly: `2026-W25`
- Monthly: `2026-06`

Verifier results: `verified`.

## CI and Release Hygiene

GitHub CLI was available but unauthenticated, so remote CI is `ci_unavailable`.

Local validation must not be represented as remote CI green.

Local validation results:

- Python: `3.15.0b2`
- Doctor: passed.
- Package version: `0.4.1`
- Focused Phase 13P tests: `9 passed`.
- v0.5 RC verifier: passed, decision `v0_5_rc_ready_with_limits`.
- Durable artifact verifier: passed, `overall_status: verified`.
- Full project tests: `611 passed`.
- Release hygiene: passed with the known non-blocking legacy tracked generated-artifact warning.
- `git diff --check`: passed with CRLF/LF normalization warnings only.
- `git diff --cached --check`: passed.

## Blocker Matrix

Primary blocker for final release publication: remote CI green evidence is missing.

Secondary cleanup: release notes must document v0.4.1 as an existing blocked historical tag.

## Final Release Readiness

v0.5 is ready for release review with limits, not final release. Final release requires CI green evidence and cleaned release notes.

## Boundaries

No tag was created, deleted, moved, or recreated. No Git write operation was executed.
