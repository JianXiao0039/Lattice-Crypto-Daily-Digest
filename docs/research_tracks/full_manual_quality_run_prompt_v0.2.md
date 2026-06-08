# Full Manual Quality Run Prompt v0.2

Purpose:

Run a heavy manual validation profile for source recovery, tests, release hygiene, and weekly handoff refresh.

Role:

- keep paused by default
- do not use as the normal daily automation path

Allowed commands:

- `python --version`
- `python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; ..."`
- `python -m lattice_digest.workflow doctor`
- `python scripts\probe_source_connectivity.py`
- `python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources`
- `scripts\recover_failed_sources_manual.bat`
- `scripts\run_weekly_handoff.bat`
- `python scripts\daily_reliability_dashboard.py`
- `scripts\run_project_tests.bat`
- `python scripts\check_release_hygiene.py`
- `git diff --check`
- `git status -sb`

Quality gates:

1. source recovery path is explicit
2. daily source-starved condition is classified correctly
3. weekly handoff path is explicit
4. tests pass
5. release hygiene passes
6. final validation summary is complete

Forbidden actions:

- no git add/commit/push/tag
- no scheduler/background jobs
- no private workspace writes
- no business-logic mutation unless explicitly requested
