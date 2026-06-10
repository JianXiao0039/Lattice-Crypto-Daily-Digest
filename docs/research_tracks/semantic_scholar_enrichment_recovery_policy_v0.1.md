# Semantic Scholar Enrichment Recovery Policy v0.1

Status: public manual enrichment recovery policy.

# Secret Handling

Only read the key from:

```text
SEMANTIC_SCHOLAR_API_KEY
```

Never print, store, log, commit, or expose the key value.

Allowed diagnostics:

- present / absent;
- non-empty;
- length.

# Failure Interpretation

| Failure | Meaning | Action |
| --- | --- | --- |
| missing key | enrichment disabled/skipped | continue digest; configure key manually if wanted |
| auth/forbidden | key or access issue | verify key manually without printing it |
| rate limit | quota/traffic issue | wait and retry manually |
| no candidate records | enrichment has nothing to enrich | recover primary sources first |
| network error | DNS/TLS/proxy/timeout issue | run source probe |

# Advisory Only

Semantic Scholar metadata is advisory context only. Citation counts and enrichment fields must not override ranking labels or research relevance.

# Manual Check

```powershell
python scripts\probe_source_connectivity.py
```

Review only `semantic_scholar_key.present` and `semantic_scholar_key.length`.

