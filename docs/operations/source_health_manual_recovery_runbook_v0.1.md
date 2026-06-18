# Source Health Manual Recovery Runbook v0.1

## Command

```powershell
python scripts\probe_source_health.py --low-load
```

This is a manual, conservative probe. It is not an ingestion bypass.

## Source-Specific Triage

### arXiv 429

Classify as `rate_limited`. Honor `Retry-After` when present. Reduce query volume and retry later manually.

### DBLP SSL/TLS

Classify certificate validation, TLS handshake, timeout, HTTP failure, and parser failure separately. Do not disable SSL verification as the default.

### Semantic Scholar

Report API key presence as boolean only. Never print the key. Distinguish missing key, auth failure, rate limit, timeout, empty response, and no candidates to enrich.

### OpenAlex

Distinguish valid empty response from network failure. Check query/date filters before classifying the source as failed.

### IACR ePrint

Distinguish latest-feed success, cache hit, failed-attempt guard, network failure, parser failure, and zero latest records. `failed/0` is not the same as no relevant papers.

### Crossref

Distinguish empty response, query mismatch, HTTP error, timeout, and parser failure.

## Compliant Recovery

Allowed:

- low request rate;
- official APIs;
- caching;
- exponential backoff;
- honoring `Retry-After`;
- source-starved reporting;
- manual retry later.

Forbidden:

- proxy rotation to evade limits;
- fake User-Agent rotation;
- CAPTCHA bypass;
- disabling SSL verification as a default;
- browser automation to bypass source protections;
- ignoring source terms or robots policies;
- aggressive repeated retries.
