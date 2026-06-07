# Weekly Handoff Pilot Run Log v0.1

Status: public manual pilot log.

# Pilot Date

2026-06-07

# Commands Run

```powershell
python --version
python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"
python -m lattice_digest.workflow doctor
scripts\run_weekly_handoff.bat
python scripts\probe_source_connectivity.py --timeout 10
```

# Weekly Handoff Result

| Field | Result |
| --- | --- |
| Weekly JSON | `data/weekly/2026-W23.json` |
| Weekly Markdown | `digests/weekly/2026-W23.md` |
| Handoff JSON | `handoffs/weekly/2026-W23-handoff-packets.json` |
| Handoff Markdown | `handoffs/weekly/2026-W23-handoff-packets.md` |
| Packet count | 20 |
| Excluded count | 1 |
| Global TODO_VERIFY count | 3 |

# Source-Starved Finding

The latest daily artifact `data/2026-06-07.json` has 0 records and all configured sources red. The weekly handoff is not empty because the W23 weekly artifact includes successful 2026-06-03 records.

# Source Probe Summary

| Source | Result |
| --- | --- |
| arxiv | reachable |
| crossref | reachable |
| dblp | HTTP 500 server_error, retryable |
| iacr_eprint | reachable; parser parsed 100 records |
| openalex | reachable |
| semantic_scholar | reachable; key present; value not printed |

# Interpretation

The current state is a mixed health state, not a total network outage:

- latest daily run is source-starved;
- weekly handoff can still produce packets from prior successful records;
- IACR latest is currently reachable but local same-day attempt guard can block normal ingestion after an earlier failure;
- Semantic Scholar is currently reachable, but enrichment was absent in the weekly artifact.

# Manual Follow-Up

- If source recovery is needed, run a bounded manual recovery with `--retry-failed-sources --include-latest-sources`.
- Do not schedule retries.
- Review handoff packets as research triage only.
- Keep TODO_VERIFY and non-claims intact.

