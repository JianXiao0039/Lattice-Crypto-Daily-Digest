# IACR Latest Recovery Policy v0.1

Status: public manual IACR recovery policy.

# Endpoint

Official RSS/latest endpoint:

```text
https://eprint.iacr.org/rss/rss.xml
```

# States

| State | Meaning | Manual action |
| --- | --- | --- |
| `cache_hit` | Same-day XML cache exists | Use cache |
| `fetched` | Feed fetched and parsed | Review source health |
| `failed` | Request failed | Run probe; inspect DNS/TLS/proxy/rate |
| `skipped_by_guard` | Failed attempt marker exists and no retry flag was passed | Run manual recovery if appropriate |
| `manual_retry` | Explicit failed-source retry | Review output and source health |
| `manual_latest_retry` | Explicit latest-source retry | Review latest feed status |
| parser failure | Feed reached but parser failed | Add fixture/test only if reproducible |

# Failed/0 Interpretation

IACR failed/0 means no usable records were produced by that run. It can mean network failure, guard skip, parser failure, or no date-window records. It is not evidence that IACR has no relevant papers.

# Manual Recovery

```powershell
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

# Non-Claims

IACR recovery does not change ranking, taxonomy, source scoring, or section classification.

