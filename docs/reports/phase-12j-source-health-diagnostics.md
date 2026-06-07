# Phase 12J Source Health Diagnostics

生成日期：2026-06-07

# Executive Summary

Phase 12J added and ran a manual source connectivity probe. The probe is diagnostic-only: it does not modify source ingestion, cache, ranking, taxonomy, section classification, query expansion, negative keyword policy, source health semantics, or release hygiene.

Current probe result:

- arXiv reachable;
- Crossref reachable;
- DBLP returned retryable HTTP 500;
- IACR ePrint RSS/latest reachable and parser parsed 100 records;
- OpenAlex reachable;
- Semantic Scholar reachable; API key present, key length 44, value not printed.

The latest daily artifact remains source-starved: `data/2026-06-07.json` contains 0 records and all configured paper sources are red. The likely immediate IACR blocker is a failed same-day attempt marker without a corresponding successful RSS cache XML.

# Probe Method

Command:

```powershell
python scripts\probe_source_connectivity.py --timeout 10
```

Probe properties:

- one lightweight request per source;
- no writes;
- no background retry loop;
- no scheduled automation;
- no API key value printed;
- official / configured source endpoints only.

# Source Probe Table

| Source | Target | Reachable | Status | Error type | Timeout | TLS | DNS | Proxy clue | Retryable | Notes |
| --- | --- | ---:| ---:| --- | ---:| ---:| ---:| ---:| ---:| --- |
| arxiv | arXiv API query | true | 200 | none | 10s | false | false | false | false | read 3557 bytes |
| crossref | Crossref works query | true | 200 | none | 10s | false | false | false | false | read 4521 bytes |
| dblp | DBLP publication search | false | 500 | server_error | 10s | false | false | false | true | Internal Server Error |
| iacr_eprint | IACR ePrint RSS/latest | true | 200 | none | 10s | false | false | false | false | read 226575 bytes; parser parsed 100 records |
| openalex | OpenAlex works query | true | 200 | none | 10s | false | false | false | false | read 16418 bytes |
| semantic_scholar | Semantic Scholar paper search | true | 200 | none | 10s | false | false | false | false | read 215 bytes; key value not printed |

# Error Classification

Current failures:

- DBLP: retryable `server_error`, HTTP 500.

Previously observed in artifacts:

- arXiv: rate limit, timeout, warning;
- Crossref: warning;
- DBLP: server_error, warning;
- IACR ePrint: warning, same-day attempt guard risk;
- OpenAlex: warning;
- Semantic Scholar: rate_limit, warning.

This means source health problems are not one single class. They include transient source failures, rate limiting, and local failed-attempt guard behavior.

# IACR Latest Diagnosis

Current probe:

- official RSS reachable: true;
- parser status: parsed;
- parsed records: 100;
- current UTC attempt marker exists: true;
- current UTC cache XML exists: false.

Interpretation:

IACR latest/RSS is not currently unreachable. The source is reachable and parser-capable. The local cache state can still cause normal ingestion to skip IACR after an earlier failed same-day attempt.

Manual recovery:

```powershell
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

Do not schedule this command.

# Semantic Scholar Diagnosis

Current probe:

- `SEMANTIC_SCHOLAR_API_KEY` present: true;
- key length: 44;
- key value: not printed;
- endpoint reachable: true;
- status code: 200;
- current rate limit: not observed;
- current auth issue: not observed.

Artifact diagnosis:

- W23 source health shows Semantic Scholar red across loaded days;
- weekly Markdown states no Semantic Scholar enrichment metadata for listed papers.

Interpretation:

Semantic Scholar being unavailable in the report means enrichment is missing. It does not affect ranking authority and does not make candidate papers irrelevant.

# Retry and Cache Behavior

IACR ePrint uses a polite once-per-UTC-day guard:

- successful fetch writes same-day XML cache;
- failed fetch leaves an attempt marker;
- normal runs do not repeatedly retry the same source on the same UTC day;
- explicit manual recovery can use `--retry-failed-sources` and `--include-latest-sources`.

This behavior is intentional politeness, but it must be visible in source-starved diagnostics.

# Recommended Manual Recovery

1. Run the probe:

```powershell
python scripts\probe_source_connectivity.py
```

2. If IACR is reachable and parser-capable but attempt marker exists without cache XML, run one manual recovery:

```powershell
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

3. If DBLP remains HTTP 500, retry later; do not treat it as a taxonomy or parser bug.

4. If arXiv or Semantic Scholar returns 429, wait and retry manually; do not create polling.

5. If several sources show DNS or TLS errors, inspect local DNS, VPN, proxy, and certificate environment.

# Risks

- Connectivity probe success does not prove full ingestion success.
- A reachable endpoint can still rate-limit larger or repeated source queries.
- Weekly handoff output can look healthy because earlier daily artifacts had records.
- Latest daily source starvation should be called out separately from weekly handoff packet counts.
- API key presence does not guarantee sufficient quota.

# TODO_VERIFY

- Whether the 2026-06-07 all-red daily run was caused primarily by transient network failure, proxy/TLS state, or retry guard behavior.
- Whether Semantic Scholar red states were rate limit only or also request-shape dependent.
- Whether DBLP HTTP 500 is query-specific or general endpoint instability.
- Whether future weekly handoff reports should embed a compact daily source-starvation warning.

