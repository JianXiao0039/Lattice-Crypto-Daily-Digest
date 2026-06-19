# Phase 14C Source Health Stability Review

Status: `source_health_long_run_policy_ready`.

## Source Policies

- arXiv: classify HTTP 429 as `rate_limited`, honor `Retry-After`, avoid tight retries, and report source-starved output if materially degraded.
- DBLP: classify SSL/TLS separately and do not disable SSL verification as production default.
- IACR ePrint: distinguish RSS/latest unreachable, parser failure, failed-attempt guard, cache hit, zero latest records, and failed/0.
- Semantic Scholar: report API key presence only as boolean; classify missing key, auth failure, rate limit, timeout, network error, empty response, and enrichment skipped.
- OpenAlex: distinguish valid empty response from network failure and avoid overinterpreting zero results.
- Crossref: distinguish empty response, query mismatch, HTTP/network failure, and parser failure.

## Anti-Abuse Compliance

Allowed mitigations remain low-load mode, conservative timeouts, official APIs, honoring Retry-After, source-starved reporting, and manual retry later.

Forbidden mitigations remain proxy rotation, fake User-Agent rotation, CAPTCHA bypass, hidden browser automation, SSL disablement as production default, aggressive repeated retries, and background retry loops.
