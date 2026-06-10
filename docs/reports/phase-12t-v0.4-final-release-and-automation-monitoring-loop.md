# Phase 12T: v0.4 Final Release and Automation Monitoring Loop

## Executive Summary

Phase 12T completes repository-side v0.4 release validation and defines a manual monitoring loop for the active Daily and Weekly modules. Daily Markdown artifacts from `2026-06-04` through `2026-06-10` are local, tracked, and present in `origin/main`. Date-targeted generation remains available, and the weekly handoff generator remains operational.

The final release status is `blocked_by_tests`, not because artifacts are missing, but because the latest observable CI evidence still contains an unresolved Ubuntu test failure. The Windows CI job and local test suite pass. No new CI run for commit `cf4d0a4` was visible on the public Actions page during this phase.

## v0.4 Final Release Decision

**Status: `blocked_by_tests`.**

Release prerequisites that pass:

- all seven daily Markdown files exist locally;
- all seven are Git-tracked;
- all seven are in `origin/main`;
- `--date DATE` appears in CLI help;
- weekly handoff generation succeeds;
- local project tests and release hygiene pass.

Blocking evidence:

- latest visible CI run `#81` for `5433a19` failed on Ubuntu during tests;
- exact failing test is unavailable from public annotations;
- no successful Linux CI result is available for the current release line.

## Daily Digest Remote Verification

Commit `cf4d0a4` is the current local and remote main head. It contains the Phase 12S submission audit. The daily Markdown artifacts for June 4-10 remain present in `origin/main`.

The corresponding JSON files remain local-only under the current ignore policy. This does not block the Markdown publication check, but it remains a post-v0.4 publication-policy risk.

## --date Support Status

- `python -m lattice_digest.run --help` includes `--date DATE`.
- `--date` and `--since` remain mutually exclusive.
- Phase 12R tests cover valid dates, invalid dates, exact Singapore-day filtering, existing `--since`, empty recovery artifacts, and all-red source-health preservation.

## Weekly Handoff Status

- `python scripts\generate_weekly_handoff.py --latest` succeeds.
- Current output remains `2026-W23` with 20 packets.
- The source weekly JSON still lists June 6 and June 7 as missing.
- Therefore the handoff is operational but stale; it is not evidence of a complete post-backfill weekly refresh.

## Automation Monitoring Loop

The monitoring loop is observational and manual. It does not create a new scheduler, retry daemon, background service, or automatic Git publication path.

After every Daily run:

1. Confirm Markdown and JSON existence or record the explicit skip/error reason.
2. Record source green/yellow/red counts and retryable failures.
3. Classify `0 records + all-red sources` as source-starved.
4. Inspect IACR latest status for fetched, cache hit, failed guard, parser failure, or zero records.
5. Inspect Semantic Scholar as available, rate-limited, auth failure, network failure, or no candidates; never print the key.
6. Use manual recovery only when source failure evidence justifies it.
7. When publication is intended, separately verify Git tracking and remote presence.

After every Weekly run:

1. Confirm loaded and missing daily dates.
2. Confirm the weekly artifact is not built from stale/source-starved input without a warning.
3. Run the handoff generator.
4. Record packet count and explain an empty packet set.
5. Keep track classification and non-claims intact.

## Daily Public Digest Run Decision

`keep_active_but_monitor`

Generation is working, remote Markdown recovery is complete, and local validation passes. Monitoring remains required for source-starved classification, new-file tracking under ignore rules, and Linux CI portability.

## Weekly Public Synthesis Run Decision

`keep_active_with_source_starved_warning`

Weekly synthesis remains useful, but stale coverage must be treated as a quality failure. The next proper weekly refresh must rebuild W23/W24 input coverage before its handoff is considered current.

## Full Manual Quality Run Policy

`keep_paused`

Use it on demand for persistent all-red source health, Linux/CI reproduction, full release validation, or weekly rebuild after backfill. Do not convert it into a regular background process.

## CI / Red X Interpretation

- Latest publicly visible CI run: `#81`, commit `5433a19`.
- Windows Python 3.11: passed.
- Ubuntu Python 3.11: failed during tests.
- Push and artifact presence succeeded independently.
- Public Actions listing did not expose a newer run for `cf4d0a4` during validation.

## Code / Docs / Script Changes

- Added `scripts/verify_v0_4_release_candidate.py`.
- Added `tests/test_v0_4_release_candidate.py`.
- Added the Phase 12T reports, final status, release notes, monitoring policies, known risks, and next-work documents.
- No ingestion, ranking, source selection, taxonomy, or fetcher behavior changed.

## Validation Results

- Python: `3.15.0b2`
- Environment import check: passed for pytest, pydantic, and Asia/Singapore
- Workflow doctor: passed; package version `0.3.3`
- v0.4 verifier: passed all local/tracked/remote daily and weekly/handoff artifact gates
- Weekly handoff: passed; W23 generated 20 packets from the existing stale weekly input
- Project tests: 446 passed
- Release hygiene: passed with the existing non-fatal legacy tracked digest notice
- `git diff --check`: passed
- `git status -sb`: completed; Phase 12T files are untracked before the release-documentation commit, while pre-existing `.gitignore`, `papers.db`, `.arts/`, and repository-local `research_artifacts/...` state remains excluded

## Known Risks

- unresolved Ubuntu CI test failure;
- ignored future daily Markdown/JSON paths;
- June 4-10 JSON not present in `origin/main`;
- source-starved status inferred rather than explicitly serialized;
- stale W23 weekly coverage;
- Semantic Scholar enrichment remains degraded on recent runs.

## Next Work Items

1. Obtain or reproduce the Ubuntu CI failure.
2. Define the official generated-artifact publication policy.
3. Refresh weekly synthesis from complete daily coverage.
4. Add explicit source-starved metadata if an additive schema change is approved.
5. Observe the next Daily and Weekly runs before declaring `final_ready`.

## TODO_VERIFY

- next GitHub Actions result after the Phase 12T commit is pushed;
- next normal Daily source-health state;
- next Weekly loaded-day coverage;
- whether the JSON publication omission is intentional;
- whether Full Manual Quality Run remains paused after Linux CI is resolved.
