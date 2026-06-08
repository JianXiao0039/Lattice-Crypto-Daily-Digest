# Daily Public Digest Run Prompt v0.2

Purpose:

Generate the public lattice/PQC daily digest with explicit reliability gates, source-health visibility, and source-starved protection.

Allowed commands:

- `python --version`
- `python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; ..."`
- `python -m lattice_digest.workflow doctor`
- `python scripts\probe_source_connectivity.py`
- `python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources`
- `scripts\daily_quality_probe.bat`
- `python scripts\daily_reliability_dashboard.py`
- `git status -sb`

Quality gates:

1. environment import check passes
2. doctor passes
3. daily workflow command completes or explicit skip reason is reported
4. generated daily JSON/Markdown exists or missing reason is explicit
5. all-red source health is not reported as normal success
6. `0 records + all-red` is labeled `source-starved`
7. IACR latest status is visible
8. Semantic Scholar status is visible without printing the key
9. reliability dashboard summary is available
10. final output includes `git status -sb`

Forbidden actions:

- no git add/commit/push/tag
- no scheduler / cron / background service / startup task
- no secret printing
- no `PhD_Application` writes
- no `D:\ResearchArtifacts` writes

Notes:

- prefer actual working commands only;
- do not reference `scripts\generate_weekly_handoff.py` from this daily module.
