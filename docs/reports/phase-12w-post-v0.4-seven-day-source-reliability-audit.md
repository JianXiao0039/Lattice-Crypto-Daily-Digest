# Phase 12W: Post-v0.4 Seven-Day Source Reliability Audit

## Executive Summary

The latest seven actual daily artifacts are 2026-06-04 through 2026-06-10. All seven predate the `v0.4.0` tag date of 2026-06-11, so this is a partial audit with zero post-tag daily observations.

Official reliability verdict: `insufficient_evidence`.

The pre-tag baseline is operationally degraded but usable: artifact completeness is 100%, but three of seven runs were all-red and source-starved. Aggregate green/yellow source reachability is 57.14%. IACR latest succeeded through fetch or cache on four of seven runs. Semantic Scholar had a key-present signal on all seven artifacts but produced no usable enrichment: three network failures and four no-candidate runs.

The latest W23 weekly synthesis is stale relative to the repaired daily evidence. It loaded five of seven W23 dates and still reports 2026-06-06 and 2026-06-07 as missing. The handoff is traceable to that weekly JSON and contains 20 packets, but it must not be treated as a complete synthesis of the repaired W23 daily set.

Automation decisions:

- Daily Public Digest Run: `keep_active_with_monitoring`;
- Weekly Public Synthesis Run: `keep_active_with_source_starved_warning`;
- Full Manual Quality Run: `run_once_for_diagnostics`;
- v0.5 transition: `insufficient_evidence` until actual post-tag daily observations exist and CI is green.

## Observation Window

- observed dates: 2026-06-04 through 2026-06-10;
- actual artifacts: seven JSON and seven Markdown files;
- tag date: 2026-06-11;
- post-tag runs: 0;
- pre-tag baseline runs: 7;
- missing observations: at least seven actual post-tag daily runs remain `TODO_VERIFY`.

## Evidence Completeness

| Evidence | Status | Limitation |
|---|---|---|
| Seven latest daily JSON files | complete | all are pre-tag |
| Matching daily Markdown | complete | all are pre-tag |
| Source-health entries | complete | artifact health is historical, not a live probe |
| IACR latest fields | complete | explicit manual retry cannot always be inferred |
| Semantic Scholar fields | partial | no enrichment-success evidence |
| W23 weekly JSON | available | stale; lists 06-06 and 06-07 as missing |
| W23 handoff JSON/Markdown | available | generated from stale W23 weekly input |
| GitHub Actions | available through public API | current HEAD CI is red; `gh` is unauthenticated |

## Seven-Day Reliability Table

| Date | Origin | MD/JSON | Raw | Normalized | Final | High | G/Y/R | Reachability | Retryable | Source-starved | IACR latest | Semantic Scholar |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 2026-06-04 | pre_tag_baseline | yes/yes | 0 | 0 | 0 | 0 | 0/0/6 | 0% | 6 | true | failed/0 | network_failure |
| 2026-06-05 | pre_tag_baseline | yes/yes | 0 | 0 | 0 | 0 | 0/0/6 | 0% | 6 | true | failed/0 | network_failure |
| 2026-06-06 | pre_tag_baseline | yes/yes | 403 | 363 | 3 | 3 | 1/5/0 | 100% | 1 | false | cache_hit/100 | no_candidates_to_enrich |
| 2026-06-07 | pre_tag_baseline | yes/yes | 0 | 0 | 0 | 0 | 0/0/6 | 0% | 6 | true | failed/0 | network_failure |
| 2026-06-08 | pre_tag_baseline | yes/yes | 383 | 346 | 6 | 5 | 2/4/0 | 100% | 1 | false | fetched/100 | no_candidates_to_enrich |
| 2026-06-09 | pre_tag_baseline | yes/yes | 403 | 363 | 2 | 0 | 1/5/0 | 100% | 1 | false | cache_hit/100 | no_candidates_to_enrich |
| 2026-06-10 | pre_tag_baseline | yes/yes | 363 | 326 | 18 | 9 | 2/4/0 | 100% | 2 | false | fetched/100 | no_candidates_to_enrich |

## Daily Artifact Completeness

- complete-artifact rate: 7/7, 100%;
- silently skipped dates inside the observed window: none;
- zero-record runs: 3/7;
- all three zero-record runs were all-red and are classified source-starved;
- their empty output is not evidence that no relevant papers existed.

## Source Health Trend

| Source | Status sequence, 06-04 to 06-10 | Interpretation |
|---|---|---|
| arxiv | red, red, yellow, red, green, yellow, yellow | recovered, then degraded by rate limit on 06-10 |
| crossref | red, red, yellow, red, green, yellow, green | recovered with intermittent degraded runs |
| dblp | red, red, yellow, red, yellow, yellow, yellow | persistent SSL-related degradation after recovery |
| iacr_eprint | red, red, green, red, yellow, green, green | latest feed recovered through fetch/cache on four runs |
| openalex | red, red, yellow, red, yellow, yellow, yellow | reachable/degraded but no retained records |
| semantic_scholar | red, red, yellow, red, yellow, yellow, yellow | network failures followed by zero-candidate operation |

Retryable URLError-style all-source failure recurred on 06-04, 06-05, and 06-07. Across source entries, 23 retryable failures were recorded. No non-retryable source error was observed by the artifact classifier.

## Source Failure Budget

This is observational guidance, not permanent business logic or a security guarantee.

| Metric | Observed | Provisional interpretation | Suggested future threshold | TODO_VERIFY |
|---|---:|---|---|---|
| Complete-artifact rate | 100% | good artifact persistence | 100% | confirm on seven post-tag runs |
| Source reachability rate | 57.14% | degraded | at least 80% green/yellow | tune after more evidence |
| All-red runs | 3/7 | too frequent | 0 in a seven-run window | network stability |
| Source-starved runs | 3/7 | too frequent | 0 in a seven-run window | guard remains active |
| Retryable source failures | 23 | high | declining trend | distinguish network, TLS, rate limit |
| IACR latest success rate | 57.14% | usable but unstable | at least 85% | post-tag evidence |
| Semantic Scholar usable-run rate | 0% | unavailable for enrichment | above 0%, then monitor | API behavior and candidates |
| W23 loaded-day consistency | 5/7, 71.43% | stale weekly snapshot | 100% after backfill refresh | regenerate weekly synthesis |

## IACR Latest Reliability

- normal fetch success: 2 runs;
- cache hit: 2 runs;
- failed/0: 3 runs;
- parser failure: not observed;
- failed-attempt guard: not explicitly recorded in these artifacts;
- explicit manual retry: cannot be proven from artifact fields alone;
- latest feed not included: 0 runs in the observed artifacts.

## Semantic Scholar Reliability

- key-present/non-empty signal: 7/7 artifacts;
- authentication failure: 0 observed;
- rate limit: 0 observed in this seven-day window;
- network failure: 3 runs;
- no candidates to enrich: 4 runs;
- enrichment success: 0 runs;
- key value and key contents were not read or printed.

Semantic Scholar unavailability is missing metadata enrichment, not evidence that papers are irrelevant.

## Weekly Handoff Consistency

- latest weekly input: `data/weekly/2026-W23.json`;
- weekly expected dates: 2026-06-01 through 2026-06-07;
- weekly loaded dates: 5/7;
- stale missing dates: 2026-06-06 and 2026-06-07, although daily artifacts now exist;
- handoff packets: 20;
- excluded records: 1;
- TODO_VERIFY items: 3;
- traceability: handoff points to the W23 weekly JSON;
- track utility: Module-SIS, Xingye bridge, AI4Lattice, ML-KEM/ML-DSA, and privacy-watchlist packets remain represented;
- consistency verdict: traceable but incomplete.

## Automation Decisions

### Daily Public Digest Run

`keep_active_with_monitoring`. Artifact persistence is reliable, but source availability is not. The source-starved guard must remain mandatory.

### Weekly Public Synthesis Run

`keep_active_with_source_starved_warning`. Weekly synthesis should be regenerated after authoritative backfills so stale missing-day coverage is not propagated into handoff packets.

### Full Manual Quality Run

`run_once_for_diagnostics`. Use it manually after the current CI fix and weekly regeneration; do not enable it as a background or scheduled service.

## v0.4 to v0.5 Go/No-Go Decision

Decision: `insufficient_evidence`.

Do not claim post-v0.4 stability from pre-tag artifacts. Obtain actual post-tag daily runs, green cross-platform CI, and a refreshed weekly synthesis before choosing `proceed_to_v0.5_track_precision` or `proceed_with_source_monitoring`.

## Changes Made

- added a read-only seven-day audit script and manual BAT wrapper;
- added focused parser/classification tests;
- added Phase 12W reports and research-track audit documents;
- no fetcher, ranking, taxonomy, scoring, scheduler, version, or tag behavior changed.

## Validation Results

See `phase-12w-seven-day-observation-log.md` for command results.

## Remaining Risks

- zero actual post-tag daily observations;
- current HEAD GitHub Actions remains red on Windows;
- W23 weekly synthesis is stale after daily backfill;
- DBLP SSL degradation recurs;
- Semantic Scholar has no usable enrichment run;
- local worktree contains unrelated existing modifications and generated files.

## TODO_VERIFY

- observe the next seven actual post-tag daily runs;
- fix and push the cross-platform reliability-dashboard implementation;
- obtain green Ubuntu and Windows CI;
- regenerate W23 weekly synthesis from all seven daily artifacts;
- confirm Semantic Scholar produces at least one usable enrichment run;
- confirm IACR latest remains stable without relying only on cache.
