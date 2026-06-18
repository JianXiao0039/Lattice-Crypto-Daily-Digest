# Phase 13L Source Health Diagnostics Log

Generated from a manual low-load run of:

```powershell
python scripts\probe_source_health.py --low-load
```

## Result

| Source | Status | HTTP | Records | Notes |
| --- | --- | ---: | ---: | --- |
| arxiv | ok | 200 | 1 | reachable |
| crossref | ok | 200 | 1 | reachable |
| dblp | ok | 200 | 1 | no TLS failure observed |
| iacr_eprint | normal_latest_feed_success | 200 | 100 | RSS/latest parsed |
| openalex | ok | 200 | 1 | reachable |
| semantic_scholar | ok | 200 | 1 | key presence true; key value not printed |

## Interpretation

This is a point-in-time source-health diagnostic. It does not prove future automation stability and should not be used as a permanent reliability threshold.

## TODO_VERIFY

- Re-run after the next Daily automation.
- Compare with CI/network results.
- Track future 429, TLS, empty-response, and parser failures separately.
