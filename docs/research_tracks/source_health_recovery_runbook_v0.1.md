# Source Health Recovery Runbook v0.1

Status: public manual recovery runbook.

# When All Sources Are Red

If arXiv, Crossref, DBLP, IACR ePrint, OpenAlex, and Semantic Scholar are all red, treat the digest as source-starved.

Do not interpret an empty digest or empty handoff as evidence that no relevant lattice/PQC papers exist.

# How to Check Network / Proxy / TLS

Run:

```powershell
python scripts\probe_source_connectivity.py
```

Check for:

- DNS errors;
- TLS errors;
- timeout;
- HTTP 429 rate limits;
- HTTP 500 source-side errors;
- proxy-related clues.

The probe is manual-only and performs one lightweight request per source.

# How to Check Source Attempt Guards

For IACR ePrint, check whether the current UTC date has:

- `cache/iacr_eprint_YYYY-MM-DD.attempt`
- `cache/iacr_eprint_YYYY-MM-DD.xml`

If an attempt marker exists but no XML cache exists, normal runs may skip IACR to avoid repeated same-day retries.

# How to Retry Failed Sources Manually

Use the existing bounded manual recovery flags:

```powershell
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

This is manual only. Do not create a scheduler or polling loop.

# How to Interpret Empty Digest

An empty digest means no usable records were produced by that run. It can be caused by:

- network failure;
- DNS/TLS/proxy issue;
- source rate limit;
- source server error;
- failed-attempt guard;
- parser failure;
- relevance filters after successful source fetch.

Use source health and connectivity probe results before drawing research conclusions.

# How to Interpret Empty Handoff

An empty handoff means the weekly handoff generator found no actionable packets in its weekly input. It does not prove no relevant papers exist.

Check:

- whether the weekly JSON has records;
- whether latest daily files are source-starved;
- whether source health caveats are red/yellow;
- whether candidates were excluded as generic/noise.

# How to Avoid Background Automation

Do not create:

- Windows Task Scheduler tasks;
- cron jobs;
- startup tasks;
- background services;
- watchers;
- automatic retries.

Recovery must stay manually triggered.

# Commands

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python --version
python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"
python -m lattice_digest.workflow doctor
python scripts\probe_source_connectivity.py
scripts\run_weekly_handoff.bat
scripts\run_project_tests.bat
python scripts\check_release_hygiene.py
git diff --check
git status -sb
```

# Non-Claims

- Source recovery does not change ranking.
- Source recovery does not change taxonomy.
- Source recovery does not change section classifier behavior.
- Source recovery does not prove paper relevance or novelty.
- Semantic Scholar enrichment is advisory only.

