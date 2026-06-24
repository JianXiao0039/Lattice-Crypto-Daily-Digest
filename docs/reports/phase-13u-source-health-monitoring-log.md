# Phase 13U Source Health Monitoring Log

## Decision

`source_health_degraded_but_explicit`

## Daily Source Health for 2026-06-20

| Source | Status | Failure / Error Type | Impact |
| --- | --- | --- | --- |
| arXiv | yellow | rate_limit | Retrieval degraded; manual low-load retry later is appropriate |
| Crossref | green | none | Healthy |
| DBLP | yellow | ssl_error | Retrieval degraded; do not disable SSL verification by default |
| IACR ePrint | yellow | cache_hit, no error | Cache-backed records available |
| OpenAlex | yellow | no final records | Empty final result is explicit, not a hard failure |
| Semantic Scholar | yellow | no final records | Enrichment unavailable or empty; API key was not printed |

## Low-Load Probe

The low-load probe respected the anti-abuse policy:

- no proxy rotation;
- no fake User-Agent rotation;
- no CAPTCHA or access-control bypass;
- one low-load request per source;
- Semantic Scholar API key presence reported without printing the key.

Probe results:

- arXiv: rate_limited, HTTP 429.
- Crossref: ok, one item.
- DBLP: TLS failure.
- IACR ePrint: ok, 100 RSS records parsed.
- OpenAlex: ok, one result.
- Semantic Scholar: ok, one candidate.
