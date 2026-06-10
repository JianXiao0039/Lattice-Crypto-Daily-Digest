# Source Recovery Pilot Run Log v0.1

Status: public pilot log.

# Pilot Date

2026-06-08

# Commands Run

```powershell
python --version
python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"
python -m lattice_digest.workflow doctor
python scripts\probe_source_connectivity.py
scripts\recover_failed_sources_manual.bat
scripts\daily_quality_probe.bat
scripts\run_project_tests.bat
python scripts\check_release_hygiene.py
git diff --check
git status -sb
```

# Pilot Result

- connectivity probe: arXiv, Crossref, DBLP, IACR, and OpenAlex reachable; Semantic Scholar returned HTTP 429 rate limit;
- IACR same-day XML cache exists and the probe/parser observed 100 RSS records;
- recovery source health showed arXiv final=5, Crossref final=1, DBLP yellow with `ssl_error`, IACR yellow with latest `cache_hit/100`;
- latest persisted daily artifact is `data/2026-06-08.json` with 6 records, 2 green sources, 4 yellow sources, 0 red sources, and `source_starved=False`;
- `data/2026-06-07.json` remains the historical source-starved reference artifact;
- weekly handoff remained non-empty with 20 packets and 1 excluded item;
- `scripts\generate_weekly_handoff.py` does not exist; the working weekly entrypoint is `scripts\run_weekly_handoff.bat` or `python -m lattice_digest.weekly_handoff --latest`.
