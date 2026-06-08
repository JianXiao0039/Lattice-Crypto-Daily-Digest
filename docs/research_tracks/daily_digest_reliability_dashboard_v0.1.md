# Daily Digest Reliability Dashboard v0.1

Status: public reliability dashboard specification.

# Purpose

Provide a repeatable, manual-only summary of daily digest health, source observability, recovery need, and weekly handoff impact.

# Working Command

```powershell
python scripts\daily_reliability_dashboard.py
```

Optional wrappers:

```powershell
scripts\daily_reliability_dashboard.bat
powershell.exe -ExecutionPolicy Bypass -File scripts\daily_reliability_dashboard.ps1
```

# Inputs

- latest `data\*.json`
- latest `data\weekly\*.json`
- latest `handoffs\weekly\*-handoff-packets.json`
- optional probe result from `scripts\probe_source_connectivity.py`
- safe environment observation for `SEMANTIC_SCHOLAR_API_KEY`

# Outputs

The dashboard prints a Markdown summary containing:

- current metrics;
- current artifact paths;
- notes;
- TODO_VERIFY queue.

# Non-Claims

- dashboard green does not mean every ingestion path is green;
- probe reachability does not prove ingest-path success;
- non-empty daily digest does not prove full weekly coverage;
- no private workspace is touched.
