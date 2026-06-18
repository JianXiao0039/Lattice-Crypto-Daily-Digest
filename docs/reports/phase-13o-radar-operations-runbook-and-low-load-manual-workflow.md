# Phase 13O Radar Operations Runbook and Low-Load Manual Workflow

## Executive Summary

Phase 13O created documentation-first manual operations runbooks for Codex, DeepSeek-Claude, and Kimi Code.

Operations runbook decision: `operations_runbook_ready`.

Operator policy decision: `codex_deepseek_kimi_policy_ready`.

Manual workflow decision: `daily_weekly_monthly_manual_workflow_ready`.

Production gate: `eligible_for_v0_5_operations_rc`, subject to normal CI/release gates.

## Phase 13N Dependency Status

Phase 13N report and RC evidence exist:

- `docs/reports/phase-13n-v0.5-release-candidate-for-paper-radar-usability.md`
- `docs/reports/phase-13n-v0.5-rc-test-log.md`
- `docs/reports/phase-13n-v0.5-rc-durable-evidence-log.md`
- `docs/research_tracks/v0.5_rc_feature_checklist_v0.1.md`

## Files Inspected

- `src/lattice_digest/workflow.py`
- `src/lattice_digest/monthly_synthesis.py`
- `src/lattice_digest/weekly_synthesis.py`
- `src/lattice_digest/recommendation_rationale.py`
- `src/lattice_digest/reading_queue.py`
- `src/lattice_digest/obsidian_scaffold.py`
- `scripts/probe_source_health.py`
- `scripts/verify_durable_artifacts.py`
- `scripts/verify_v0_5_rc.py`
- `scripts/export_reading_queue.py`
- `scripts/export_obsidian_notes.py`
- `scripts/run_project_tests.bat`
- `README.md`
- `docs/index.md`
- `AGENTS.md`

`src/lattice_digest/obsidian_export.py` is not present; the repository uses `obsidian_scaffold.py`.

## SOP Status

| Area | Status |
| --- | --- |
| Daily SOP | ready |
| Weekly SOP | ready |
| Monthly SOP | ready, module entrypoint |
| Full run SOP | ready, manual sequence only |
| Specific date backfill | ready |
| Specific time range | ready with documented CLI limits |
| Source health | ready |
| Durable artifact verification | ready |
| Reading queue / Obsidian export | ready |

## Operator Policies

Codex remains the primary engineering operator. DeepSeek-Claude and Kimi Code are backup/manual operators and must not own release operations, Git write operations, private-path access, or broad production code changes.

## Anti-Abuse and Low-Load Policy

The runbooks recommend low request rate, official APIs, caching, backoff, `Retry-After`, source-starved reporting, and manual retry later. They forbid proxy rotation, fake User-Agent rotation, CAPTCHA bypass, default SSL disabling, hidden browser bypass, source-term evasion, and aggressive retries.

## No-Background-Automation Confirmation

The runbooks do not create or recommend Task Scheduler tasks, cron jobs, startup tasks, watchers, background services, or automatic future runs.

## v0.5 RC Relation

Phase 13O adds the operator-facing layer needed for v0.5 paper-radar usability operations. It does not change radar semantics and does not replace CI, release hygiene, or durable artifact gates.

## Changes Made

Documentation and focused runbook-policy tests only. No production fetcher, ranking, taxonomy, query, negative-keyword, Daily/Weekly trigger, or release-tag logic was changed.

## Validation Results

- Python: `3.15.0b2`
- Doctor: passed.
- Package version: `0.4.1`
- Focused Phase 13O tests: `9 passed`.
- Full project tests: `602 passed`.
- Release hygiene: passed with the known non-blocking legacy tracked generated-artifact warning.
- `git diff --check`: passed; only pre-existing CRLF/LF normalization warnings were reported for Phase 13H files.
- Git write operations: none.

## TODO_VERIFY

- Re-check remote GitHub Actions with authenticated `gh` or GitHub UI.
- Re-run one manual full sequence before final v0.5 release tagging.
- Confirm future operators follow the handoff template exactly.
