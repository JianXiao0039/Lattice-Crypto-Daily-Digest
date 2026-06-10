# Source Health Recovery Runbook v0.2

Status: public manual recovery runbook.

# When All Sources Are Red

If arXiv, Crossref, DBLP, IACR ePrint, OpenAlex, and Semantic Scholar are all red, label the run source-starved.

Do not interpret an empty digest or empty handoff as evidence that no relevant lattice/PQC papers exist.

# Source Failure Classes

Use the source connectivity probe to distinguish:

- `dns`
- `tls`
- `proxy`
- `timeout`
- `http_status`
- `rate_limit`
- `api_key_or_auth`
- `parser`
- `unknown_url_error`
- `reachable`

# How to Check Network / Proxy / TLS

```powershell
python scripts\probe_source_connectivity.py
```

Inspect:

- `failure_class`;
- `error_type`;
- `status_code`;
- `tls_error`;
- `dns_error`;
- `proxy_related_clue`;
- `retryable`.

# How to Check IACR Attempt Guards

For the current UTC date, inspect:

- `cache/iacr_eprint_YYYY-MM-DD.attempt`
- `cache/iacr_eprint_YYYY-MM-DD.xml`

Attempt marker without XML cache means manual retry may be needed.

# How to Retry Failed Sources Manually

Use either:

```powershell
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

or:

```cmd
scripts\recover_failed_sources_manual.bat
```

These commands are manual-only. Do not schedule them.

# How to Interpret Empty Digest

An empty digest after all-red source health means source-starved. It can be caused by DNS, TLS, proxy, timeout, HTTP status, rate limit, API-key/auth, parser failure, attempt guard, or unknown URLError.

# How to Interpret Empty Handoff

An empty handoff means no actionable packet was produced from the weekly input. If source health was red, label the handoff source-starved.

# How to Avoid Background Automation

Do not create:

- Windows Task Scheduler tasks;
- cron jobs;
- startup tasks;
- background services;
- watchers;
- automatic retries.

# Commands

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python --version
python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"
python -m lattice_digest.workflow doctor
python scripts\probe_source_connectivity.py
scripts\recover_failed_sources_manual.bat
scripts\run_weekly_handoff.bat
scripts\run_project_tests.bat
python scripts\check_release_hygiene.py
git diff --check
git status -sb
```

# Non-Claims

Source recovery does not change ranking, taxonomy, section classifier behavior, relevance scoring, novelty claims, or security claims.

