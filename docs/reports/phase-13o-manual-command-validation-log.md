# Phase 13O Manual Command Validation Log

## Commands Inspected

- `python -m lattice_digest.workflow --help`
- `python -m lattice_digest.workflow daily --help`
- `python -m lattice_digest.workflow weekly --help`
- `python -m lattice_digest.workflow full --help`
- `python -m lattice_digest.workflow status --help`
- `python -m lattice_digest.workflow doctor --help`
- `python -m lattice_digest.run --help`
- `python -m lattice_digest.monthly_synthesis --help`
- `python scripts\probe_source_health.py --help`
- `python scripts\verify_durable_artifacts.py --help`
- `python scripts\export_reading_queue.py --help`
- `python scripts\export_obsidian_notes.py --help`

## Findings

- Daily supports `--since` and `--date`.
- Daily does not expose `--start` / `--end`; the time-range runbook documents this limitation.
- Weekly supports dry-run planning, `--execute`, `--from-date`, `--to-date`, and `--low-load`.
- Workflow supports `daily`, `weekly`, `full`, `status`, and `doctor`.
- Monthly synthesis is implemented as `python -m lattice_digest.monthly_synthesis --month YYYY-MM`.
- Source-health, durable artifact, reading queue, and Obsidian export scripts are present.

## Decision

`daily_weekly_monthly_manual_workflow_ready`

## Validation Results

- Focused runbook tests: `9 passed`.
- Full project tests: `602 passed`.
- Release hygiene: passed.
- `git diff --check`: passed with CRLF/LF normalization warnings only.
