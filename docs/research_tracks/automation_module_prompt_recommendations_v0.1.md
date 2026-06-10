# Automation Module Prompt Recommendations v0.1

Status: public prompt recommendation doc for manual UI updates.

# Daily Public Digest Run

Purpose:
Generate the public lattice/PQC daily digest with clear source-health reporting and source-starved interpretation.

Allowed commands:
`python --version`
`python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; ..."`
`python -m lattice_digest.workflow doctor`
`python scripts\probe_source_connectivity.py`
`python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources`
`scripts\daily_quality_probe.bat`
`git status -sb`

Forbidden actions:
no git add/commit/push/tag
no Task Scheduler/cron/background services/startup tasks
no secret printing
no `PhD_Application` writes
no `D:\ResearchArtifacts` writes

Quality gates:
environment ok
doctor passes
source health visible
source-starved classified explicitly
IACR latest state visible
Semantic Scholar enrichment visibility without key leakage

# Weekly Public Synthesis Run

Purpose:
Generate weekly public synthesis from current weekly artifacts and then generate weekly handoff packets.

Allowed commands:
`python -m lattice_digest.workflow weekly --low-load --skip-hygiene`
`python -m lattice_digest.weekly_handoff --latest`
`scripts\run_weekly_handoff.bat`
`git status -sb`

Forbidden actions:
no git add/commit/push/tag
no private workspace writes
no background scheduling

Quality gates:
weekly input coverage reviewed
source-starved weekly interpretation explicit
handoff output generated or missing command documented

# Full Manual Quality Run

Purpose:
Perform heavier manual validation when source recovery, tests, release hygiene, and handoff refresh are needed.

Allowed commands:
`python --version`
`python -m lattice_digest.workflow doctor`
`python scripts\probe_source_connectivity.py`
`scripts\recover_failed_sources_manual.bat`
`scripts\run_project_tests.bat`
`python scripts\check_release_hygiene.py`
`git diff --check`
`git status -sb`

Forbidden actions:
no git add/commit/push/tag
no scheduler/background jobs
no private workspace writes

Quality gates:
manual recovery path explicit
tests pass
release hygiene passes
handoff available if weekly artifacts exist

