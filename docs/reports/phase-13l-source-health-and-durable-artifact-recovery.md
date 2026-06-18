# Phase 13L Source Health and Durable Artifact Recovery

## Executive Summary

Phase 13L added manual source-health diagnostics and a durable Daily/Weekly/Monthly artifact verifier. The changes are additive and do not alter source fetchers, source-health semantics, ranking, taxonomy, query expansion, Daily/Weekly/Monthly scheduling, or recommendation-rationale behavior.

Source health decision: `source_health_diagnostics_ready`.

Durable artifact decision: `daily_weekly_monthly_artifacts_verified`.

Anti-abuse compliance decision: `compliant_low_load_policy_ready`.

Production gate: `eligible_for_v0_5_reliability_rc` pending normal CI/release-gate evidence.

## Phase 13K Dependency Status

Phase 13K monthly synthesis outputs were present:

- `docs/reports/phase-13k-monthly-lattice-paper-radar-synthesis.md`
- `docs/research_tracks/v0.5_monthly_source_health_summary_v0.1.md`
- `data/monthly/2026-06.json`
- `digests/monthly/2026-06.md`

## Files Inspected

- `scripts/probe_source_connectivity.py`
- `src/lattice_digest/http.py`
- `src/lattice_digest/sources/base.py`
- `src/lattice_digest/monthly_synthesis.py`
- `src/lattice_digest/weekly_synthesis.py`
- `src/lattice_digest/digest.py`
- `audits/source-health/*.json`
- `data/2026-06-15.json`
- `digests/2026-06-15.md`
- `data/weekly/2026-W25.json`
- `digests/weekly/2026-W25.md`
- `data/monthly/2026-06.json`
- `digests/monthly/2026-06.md`

## Source-Health Status by Source

Manual low-load probe result:

| Source | Status | Diagnosis |
| --- | --- | --- |
| arxiv | ok | HTTP 200, one entry |
| crossref | ok | HTTP 200, one item |
| dblp | ok | HTTP 200, one hit; no SSL failure observed |
| iacr_eprint | normal_latest_feed_success | HTTP 200, 100 parsed latest records |
| openalex | ok | HTTP 200, one result |
| semantic_scholar | ok | HTTP 200, one candidate; key presence reported without printing key |

## arXiv 429 Diagnosis and Policy

The new probe classifies HTTP 429 as `rate_limited`, captures `Retry-After` when present, and treats it as retryable. The recovery policy is to wait, reduce query volume, and retry manually.

## DBLP SSL Diagnosis and Policy

DBLP SSL failures are classified as `ssl_failure` / `tls`. SSL verification remains enabled by default. Phase 13L observed DBLP healthy locally.

## Semantic Scholar Diagnosis

Semantic Scholar key presence is reported as a boolean only. The key value is not printed. Missing key, auth failure, rate limit, timeout, empty response, and candidate-bearing success are separable.

## OpenAlex Diagnosis

OpenAlex empty valid responses are classified as `empty_response`, distinct from network failure. Phase 13L observed one result.

## IACR Recovery Diagnosis

IACR latest is classified into normal latest success, cache hit, failed-attempt guard, network failure, parser failure, or zero latest records. Phase 13L observed `normal_latest_feed_success` with 100 records.

## Crossref Status

Crossref was reachable with one parsed item. Empty valid responses remain separate from network failures.

## Durable Artifact Verification

Command:

```powershell
python scripts\verify_durable_artifacts.py --date 2026-06-15 --week 2026-W25 --month 2026-06
```

Result: `verified`.

| Artifact | Target | Result |
| --- | --- | --- |
| Daily | 2026-06-15 | Markdown/JSON present, JSON parseable, source health present |
| Weekly | 2026-W25 | Markdown/JSON present, source-health summary and coverage present |
| Monthly | 2026-06 | Markdown/JSON present, input daily files, missing days, and source-starved field present |

## Source-Starved Reporting

The verifier marks zero-record all-red Daily runs as source-starved and requires an explicit Markdown or JSON marker. Monthly source-health summaries must include a `source_starved` field.

## Tests

Added focused tests for:

- source-health probe sanitization;
- HTTP 429 classification;
- DBLP SSL classification;
- Semantic Scholar missing key/auth/rate-limit separation;
- OpenAlex empty response classification;
- IACR failed/zero latest interpretation;
- durable artifact verification;
- source-starved reporting.

## v0.4.1 Release Relation

This phase improves reliability diagnostics and artifact verification. It does not create or move release tags and does not by itself resolve any external CI or release-tag gate.

## v0.5 Gate Decision

`eligible_for_v0_5_reliability_rc`, subject to CI and continued source-health observations.

## TODO_VERIFY

- Re-run source probe after the next Daily automation.
- Verify source-health behavior in GitHub Actions.
- Confirm Semantic Scholar under candidate-bearing enrichment load.
- Confirm future source-starved Daily output includes explicit caveats.
