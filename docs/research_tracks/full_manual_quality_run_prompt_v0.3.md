# Full Manual Quality Run Prompt v0.3

Project path:

`D:\Code\CodexProjects\lattice-crypto-daily-digest`

Role:

- paused
- heavy manual validation profile
- not the default daily automation path

Use it when:

- source recovery is needed
- repeated all-red or source-starved results appear
- project tests should be rerun
- release hygiene should be checked
- weekly handoff should be replayed after degraded daily runs

Allowed commands:

- `python --version`
- `python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"`
- `python -m lattice_digest.workflow doctor`
- `python scripts\probe_source_connectivity.py`
- `python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources`
- `scripts\recover_failed_sources_manual.bat`
- `scripts\run_weekly_handoff.bat`
- `python scripts\print_current_reliability_baseline.py`
- `scripts\run_project_tests.bat`
- `python scripts\check_release_hygiene.py`
- `git diff --check`
- `git status -sb`

Forbidden commands and actions:

- no `git add`
- no `git commit`
- no `git push`
- no `git tag`
- no scheduler / background job / startup task
- no `PhD_Application` writes
- no `D:\ResearchArtifacts` writes

Required reporting:

1. source recovery outcome
2. Daily / Weekly artifact state
3. baseline status
4. tests
5. release hygiene
6. `git diff --check`
7. `git status -sb`
