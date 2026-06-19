# Source Health Failure Interpretation Table v0.1

Status: `source_health_failure_interpretation_ready`.

| Source | Failure/status | Interpretation | Operator action |
| --- | --- | --- | --- |
| arXiv | `rate_limited`, HTTP 429 | source is rate limiting; not evidence of no papers | honor `Retry-After` if visible; rerun later in low-load mode |
| arXiv | timeout/network | source degraded | mark source-starved if material; do not tight-loop retries |
| DBLP | `ssl_failure` / TLS | local CA/proxy/TLS or remote handshake issue | do not disable SSL verification as production default; document local remediation |
| DBLP | parser failure | endpoint reached but response parse failed | report parser failure separately from TLS/network |
| IACR ePrint | RSS/latest unreachable | source unavailable | do not claim IACR has no relevant papers |
| IACR ePrint | `failed_attempt_guard` | retry guard active | report guard state and retry manually later |
| IACR ePrint | cache hit | cached recovery path used | report cache freshness if available |
| IACR ePrint | zero latest records | feed parsed but no latest records | distinguish from failed/0 |
| Semantic Scholar | `missing_key` | enrichment key absent | report boolean key presence only; continue radar |
| Semantic Scholar | auth failure | key rejected or access denied | never print key; mark enrichment unavailable |
| Semantic Scholar | rate limited | source throttled | respect limit; retry later manually |
| Semantic Scholar | empty response | valid response with no candidates | distinguish from network failure |
| OpenAlex | empty response | valid response with zero results | check query/date filter; do not overinterpret |
| OpenAlex | network failure | source degraded | report source-health caveat |
| Crossref | empty response | valid zero result or query mismatch | distinguish from network failure |
| Crossref | network/parser failure | source degraded | report reliability impact |

All interpretations must preserve source-starved reporting and avoid anti-bot bypass.
