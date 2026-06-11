# Phase 12X: Source Failure Budget Freeze and v0.5 Track Precision Scope

## Executive Summary

Phase 12X freezes metric definitions, failure classes, provisional warning bands, escalation rules, and evidence requirements. It does not freeze the Phase 12W observed rates as permanent thresholds.

The preferred Full Manual Quality Run was safely blocked. `workflow full --execute --generate-notes` would write the current daily JSON/Markdown, `papers.db`, weekly artifacts, exports, reading queue, notes, and workflow manifests. The worktree already contains an unstaged source fix and a modified `papers.db`, so a full run would mix diagnostic outputs with unrelated local state and could overwrite or create authoritative artifacts without clean attribution.

A read-only source connectivity probe was used instead. Five of six sources were reachable: arXiv, Crossref, DBLP, IACR ePrint, and OpenAlex returned HTTP 200. IACR RSS parsed 100 records. Semantic Scholar returned HTTP 429 with a non-empty key signal; no key value was printed. This improves the immediate connectivity interpretation but does not replace an actual Daily run.

Decision: `proceed_with_track_precision_design`. Broad v0.5 implementation remains gated by actual post-tag evidence, a refreshed weekly synthesis, and green Windows CI.

## Phase 12W Evidence Review

- evidence type: `pre_tag_baseline`;
- daily artifacts: 7/7 Markdown and JSON;
- post-tag Daily runs: 0;
- source reachability: 57.14%;
- source-starved runs: 3/7;
- retryable source failures: 23;
- IACR latest usable rate: 57.14%;
- Semantic Scholar usable rate: 0%;
- weekly coverage completeness: 71.43%;
- handoff packets: 20 and traceable to W23 input;
- Ubuntu CI: pass;
- Windows CI: fail;
- local repository tests at Phase 12W: 449 passed.

## Why the Budget Is Provisional

The observed window predates the `v0.4.0` tag. It contains normal-network, degraded-network, and source-starved states, but no actual post-tag Daily run and no post-tag Weekly run. Therefore the rates are useful for warning-band design, not for permanent service-level thresholds.

Reliability measures whether evidence was obtained and artifacts were generated. It does not measure paper relevance, ranking quality, novelty, or research-track usefulness. A highly reachable source can produce irrelevant papers; a degraded source can hide relevant papers.

## Frozen Metric Schema

The schema freezes these fields:

- observation period and evidence type;
- daily artifact completeness;
- source reachability;
- all-red and source-starved run counts;
- retryable and non-retryable failure counts;
- IACR latest usable rate;
- Semantic Scholar enrichment usable rate;
- weekly coverage completeness;
- handoff traceability;
- Windows and Ubuntu CI status;
- confidence level and TODO_VERIFY.

Definitions are frozen for consistent observation. Values and warning thresholds remain provisional.

## Provisional Failure Budget

| Band | Meaning | Provisional trigger examples | Required response |
|---|---|---|---|
| `healthy_observation` | artifacts and sources are observably healthy | complete artifacts, no source-starved run, high green/yellow coverage | continue monitoring |
| `degraded_but_usable` | output remains usable with partial degradation | complete artifacts, yellow sources, no silent omission | keep automation active with warnings |
| `source_starved_warning` | discovery evidence is not trustworthy | 0 records plus all-red sources | label source-starved and manually recover |
| `diagnostic_required` | repeated or structural reliability failure | missing artifact, repeated source-starved runs, persistent IACR/Semantic failure | run manual diagnostics |
| `insufficient_evidence` | sample cannot support a stability conclusion | no post-tag runs or missing required evidence classes | do not promote thresholds |

Suggested numeric values in the supporting policy are provisional documentation only and are not production logic.

## Full Manual Diagnostic Result

Status: `safely_blocked_dirty_worktree`.

Reasons:

1. `src/lattice_digest/reliability_dashboard.py` has an unstaged code fix;
2. `papers.db` is already modified;
3. `.gitignore` and unrelated untracked paths are present;
4. the full workflow would perform current-date network fetching and write multiple generated artifact families;
5. attribution of new source-health or database changes would be unreliable.

Fallback connectivity probe:

| Source | Result |
|---|---|
| arXiv | reachable, HTTP 200 |
| Crossref | reachable, HTTP 200 |
| DBLP | reachable, HTTP 200 |
| IACR ePrint | reachable, HTTP 200, parsed 100 records |
| OpenAlex | reachable, HTTP 200 |
| Semantic Scholar | HTTP 429 rate limit, retryable |

The probe changes the immediate interpretation from generalized network failure to one source-specific rate-limit problem. It does not demonstrate end-to-end Daily reliability.

## Source Failure Escalation Policy

1. Always label 0 records plus all-red sources as source-starved.
2. Keep Daily active with monitoring for isolated yellow-source degradation.
3. Manually probe connectivity after an all-red run.
4. Run explicit manual recovery only after confirming the worktree and authoritative artifact policy.
5. Escalate to Full Manual Quality Run after repeated source-starved runs, missing artifacts, stale weekly coverage, or CI/local disagreement.
6. Keep retries bounded and manual; create no scheduler or retry service.
7. Treat Semantic Scholar enrichment failure as metadata degradation, not paper irrelevance.
8. Separate source reliability findings from track relevance and ranking review.

## Post-Tag Evidence Requirements

Permanent thresholds require at minimum:

- multiple actual post-tag Daily runs, with seven as the initial observation window;
- at least one actual post-tag Weekly synthesis and handoff;
- both normal-network and degraded-network observations;
- IACR fetch and cache observations;
- at least one Semantic Scholar candidate-bearing observation;
- green Windows and Ubuntu CI evidence;
- no silent Markdown or JSON omissions;
- traceable weekly coverage after backfill;
- manual review confirming metrics are not conflated with relevance quality.

## v0.5 Track Precision Scope

### Track 1: Module-SIS Chameleon Hashing and Sanitizable Signatures

Focus on lattice/SIS/Module-SIS anchored chameleon hashing, sanitizable signatures, commitments, exposure/adaptation behavior, trapdoor collision mechanisms, parameterization, and reproducibility.

### Track 2: Xingye Lu Technical Bridge

Track lattice ring and linkable signatures, hash-then-one-way signatures, programmable hash functions, and privacy-preserving lattice primitives. These are topic bridges only; professor-specific authorship, affiliation, or fit remains `TODO_VERIFY`.

### Track 3: AI4Lattice Longline

Focus on sparse LWE/RLWE/MLWE attacks, learning-guided coordinate selection, BKZ/primal/dual/hybrid interfaces, and Swin-guided ranking. Require explicit lattice-attack anchoring and classical baselines.

### Track 4: Core PQC Background

Keep ML-KEM, ML-DSA, threshold PQC, implementation, and parameterization papers when they support concrete research maturity or artifact work.

## v0.5 Non-Goals

- no private PhD application content;
- no email generation;
- no replacement for interactive deep reading;
- no scheduler or background service;
- no global ranking, taxonomy, query, or negative-keyword overhaul;
- no unsupported AI insertion into Module-SIS work;
- no professor-specific claims without verification.

## Track Evaluation Protocol

For each track:

1. draw a fixed precision sample from generated records;
2. manually label true positives and false positives;
3. review a query/source sample for false negatives;
4. require a paper-to-track explanation with explicit lattice/PQC anchors;
5. assess handoff usefulness for related work, implementation, proof, or parameterization;
6. distinguish advisor relevance and ResearchArtifacts utility from verified paper facts;
7. record TODO_VERIFY and non-claims;
8. compare results before changing production classification policy.

## v0.5 Go/No-Go Decision

`proceed_with_track_precision_design`.

Allowed now: schemas, labeled evaluation sets, review templates, and implementation plans.

Gated: production classification changes, threshold changes, query expansion, taxonomy changes, and automated ResearchArtifacts handoff changes.

## Windows CI Risk

Latest public Actions evidence for HEAD `fce3eae`:

- Ubuntu: success;
- Windows: failure.

This remains a release/maintenance blocker. Phase 12X does not duplicate the Phase 12U fix work or weaken tests.

## Validation Results

See `phase-12x-full-manual-diagnostic-run-log.md` for commands and final validation.

## TODO_VERIFY

- seven actual post-tag Daily runs;
- one complete post-tag Weekly synthesis;
- green Windows CI after the existing path fix is committed;
- Semantic Scholar candidate-bearing behavior after rate-limit recovery;
- safe Full Manual Quality Run from a clean, attributable worktree;
- precision and false-negative samples for every v0.5 track.
