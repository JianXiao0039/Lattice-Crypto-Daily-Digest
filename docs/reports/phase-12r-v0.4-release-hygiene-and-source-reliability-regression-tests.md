# Phase 12R: v0.4 Release Hygiene and Source Reliability Regression Tests

## Executive Summary

Phase 12R adds deterministic one-day generation through `--date YYYY-MM-DD` while preserving the existing `--since` workflow. The two options are mutually exclusive. A date-targeted run uses the exact Asia/Singapore calendar day, writes the normal Markdown and JSON artifacts, and still writes valid artifacts when the result is empty or source-starved.

The missing local dates `2026-06-06` and `2026-06-09` were regenerated manually. They produced 3 and 2 records respectively. Both runs had IACR ePrint available from cache, Semantic Scholar enabled but without returned candidates, and a retryable DBLP TLS failure. Neither run was source-starved.

## Implementation Scope

- Added `--date YYYY-MM-DD` to `python -m lattice_digest.run`.
- Rejected `--date` with `--since` through an argparse mutually exclusive group.
- Rejected `--date` with legacy `--target-date`.
- Preserved the default `--since 36h` behavior when neither date option is supplied.
- Applied an exact Asia/Singapore midnight-to-midnight filter for `--date`.
- Preserved existing output, source-health, retry, latest-source, and database semantics.
- Added focused CLI, recovery-policy, and source-starved tests.

## Files Changed

### Code

- `src/lattice_digest/run.py`: date parsing, exact-day coverage, conflict handling, and effective lookback metadata.

### Tests

- `tests/test_date_targeted_backfill_cli.py`
- `tests/test_missing_digest_recovery_policy.py`
- `tests/test_source_starved_daily_artifact_policy.py`

### Documentation

- `docs/reports/phase-12r-date-targeted-backfill-audit.md`
- `docs/research_tracks/date_targeted_backfill_usage_v0.1.md`
- `docs/research_tracks/v0.4_source_reliability_regression_tests_v0.1.md`
- `docs/research_tracks/v0.4_release_hygiene_checklist_v0.1.md`
- `docs/research_tracks/missing_digest_recovery_policy_v0.1.md`
- `docs/research_tracks/source_starved_daily_artifact_policy_v0.2.md`

## CLI Behavior

```powershell
python -m lattice_digest.run --date 2026-06-06 --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

The command targets `2026-06-06T00:00:00+08:00` through `2026-06-07T00:00:00+08:00`. Invalid ISO dates fail during argument parsing. Supplying `--date` together with `--since` fails with a clear mutually-exclusive-arguments error.

## Source Reliability Regression Coverage

The focused tests verify:

1. Valid `YYYY-MM-DD` input is accepted.
2. Invalid dates are rejected.
3. `--date` and `--since` cannot be combined.
4. Existing `--since` parsing remains available.
5. Exact-day filtering excludes records outside the requested Singapore calendar day.
6. Empty date-targeted runs still write JSON and Markdown.
7. All-red source failures remain visible in source health and do not suppress artifacts.
8. Test outputs remain inside the configured repository root and do not target private paths.

## Backfill Result

| Date | Records | Source health | Source-starved | IACR latest | Semantic Scholar |
|---|---:|---|---|---|---|
| 2026-06-06 | 3 | 1 green, 5 yellow, 0 red | false | `cache_hit`, 100 records | yellow, API key used, 0 candidates |
| 2026-06-09 | 2 | 1 green, 5 yellow, 0 red | false | `cache_hit`, 100 records | yellow, API key used, 0 candidates |

DBLP reported a retryable `ssl_error` on both runs. The runs remain usable because IACR supplied date-matching records, but the source-health degradation must remain visible.

## Weekly Handoff

`python scripts\generate_weekly_handoff.py --latest` regenerated `handoffs/weekly/2026-W23-handoff-packets.json` and `.md` with 20 packets. The generator selected the latest existing weekly input, which is still `2026-W23`; this does not constitute a new `2026-W24` weekly synthesis.

## Release Hygiene

- Do not infer release readiness solely from successful backfill.
- Review `papers.db` and generated digest/data artifacts separately from code and docs.
- Do not commit caches, logs, secrets, temporary test directories, or private material.
- Confirm all required generated artifacts are intentionally included or intentionally ignored before a future commit.
- No Git staging, commit, push, or tag operation belongs to Phase 12R.

## Validation Results

- Python: `3.15.0b2`
- Environment imports: passed
- Workflow doctor: passed
- Focused Phase 12R tests: 8 passed
- Project tests: 443 passed
- Release hygiene: passed; the tool reported existing legacy tracked digest artifacts as a non-fatal repository-cleanup notice
- `git diff --check`: passed with no whitespace errors
- `git status -sb`: completed; the worktree contains pre-existing modified and untracked Phase 12G-12L files in addition to Phase 12R changes

## Risks and TODO_VERIFY

- TODO_VERIFY whether DBLP TLS failures persist on the next normal daily run.
- TODO_VERIFY whether Semantic Scholar returns enrichment candidates when matching records are available.
- TODO_VERIFY whether a separate weekly synthesis command should generate `2026-W24` after the daily backfill.
- TODO_VERIFY the intended future commit policy for generated `data/`, `digests/`, `handoffs/`, and `papers.db`.
- The legacy `--target-date` behavior remains supported and is not redefined by this phase.
