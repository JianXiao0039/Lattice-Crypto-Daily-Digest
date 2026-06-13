# Phase 13C Human Annotation Pack and Shadow Track Classifier Design

## Executive Summary

Phase 13B dependencies were present and consistent: 62 repository-grounded records, all awaiting user review, with zero human-gold labels. Phase 13C created a 25-record disagreement-prioritized annotation pack and a manually invoked shadow classifier isolated from production.

No source ingestion, source health, ranking, Daily, Weekly, handoff, or production track assignment behavior changed. The shadow output is an evaluation artifact, not an accuracy claim.

## Phase 13B Dependency Status

All required Phase 13B reports, sample files, annotation queue, coverage report, offline results, candidate rules, and production-gate decision were available. The sample contains 62 unique records and no user-confirmed or user-corrected labels.

Decision: `annotation_pack_ready_with_coverage_gaps`.

## Human Annotation Pack

- Pack size: 25.
- Queued for user review: 25.
- User confirmed: 0.
- User corrected: 0.
- Primary-track disagreements: 19.
- Production-labeled/shadow-irrelevant cases: 6.

The queue prioritizes disagreements, low-confidence cases, ambiguous/multi-track cases, likely false positives/negatives, and known track-boundary risks. Human-gold fields remain blank.

## Shadow Classifier Design

The classifier reads only the Phase 13B sample and experimental rules. It emits explanations and disagreement categories under `audits/shadow/`. It is not imported by production code and is not called by Daily, Weekly, or scheduled automation.

The first rule pass revealed Track D bucket drift. Broad direct terms were removed, and a label-leakage audit removed prior annotation explanations from input features. Even after correction, Track D receives 46/62 predictions and Track B receives none. This limits the current design.

Decision: `shadow_design_ready_with_limits`.

## Evaluation Rules

Only user-confirmed or user-corrected entries may support true precision/recall/F1. With zero valid gold labels, Phase 13C reports agreement/disagreement and review priority only.

## ARS Role

Academic Research Suite was used only for inline experiment-design and track-boundary review. It did not assign final labels, modify production classification, retrieve papers, become a dependency, or run background agents/hooks/external models.

## Production Gate

`blocked_by_multiple_conditions`

Blocking conditions include no user-reviewed gold labels, no valid human-gold metrics, Track D drift, Track B under-coverage, existing CI/release gates, and separate durable-run requirements.

## Files Added

- Experimental rules and two manual scripts.
- Three focused test files.
- Human annotation pack in Markdown, CSV, and JSON.
- Annotation instructions, adjudication, conflict, and progress documents.
- Shadow contract, non-integration, evaluation, disagreement, and production-gate documents.
- Phase 13C main, evaluation, invariant, and ARS review reports.

## TODO_VERIFY

- User review of the 25 queued records.
- Track B recall after technical examples receive human labels.
- Track D false-positive rate on user-reviewed evidence.
- Whether a future shadow pilot meets human-gold metric and CI gates.
