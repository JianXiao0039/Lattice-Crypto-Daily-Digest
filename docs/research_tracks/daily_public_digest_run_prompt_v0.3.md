# Daily Public Digest Run Prompt v0.3

Project path:

`D:\Code\CodexProjects\lattice-crypto-daily-digest`

Python policy:

- Use the current validated environment.
- `Python 3.15.0b2` is acceptable only if:
  - `pytest` imports
  - `pydantic` imports
  - `ZoneInfo("Asia/Singapore")` works
  - `python -m lattice_digest.workflow doctor` passes

Purpose:

Generate the public lattice/PQC daily digest with explicit source health, reliability reporting, and source-starved false-success protection.

Allowed commands:

- `python --version`
- `python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"`
- `python -m lattice_digest.workflow doctor`
- `python scripts\probe_source_connectivity.py`
- `python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources`
- `scripts\daily_quality_probe.bat`
- `python scripts\daily_reliability_dashboard.py`
- `git status -sb`

Forbidden commands and actions:

- no `git add`
- no `git commit`
- no `git push`
- no `git tag`
- no Task Scheduler
- no cron
- no background service
- no startup task
- no `PhD_Application` writes
- no `D:\ResearchArtifacts` writes
- no secret printing

Required reporting:

1. source health per source
2. source-starved classification
3. IACR latest status
4. Semantic Scholar status without printing the key
5. final artifact existence
6. `git status -sb`
7. validation summary

Source-starved false-success guard:

- `0 records + all-red sources = source-starved`
- source-starved is not a successful paper-discovery result
- empty digest under source-starved input is not evidence of no relevant lattice/PQC papers
- recovery must remain manual-only

IACR latest reporting:

- report whether latest feed is reachable
- report parser status if available
- report `cache_hit`, `fetched`, `failed-attempt guard`, or `0 records` explicitly

Semantic Scholar reporting:

- report key presence only as boolean and safe length
- never print the key
- distinguish missing key / auth failure / rate limit / no candidates / enrichment success

Final requirement:

- end with `git status -sb`
- do not touch private directories
- do not create or modify automation schedules from the repository
