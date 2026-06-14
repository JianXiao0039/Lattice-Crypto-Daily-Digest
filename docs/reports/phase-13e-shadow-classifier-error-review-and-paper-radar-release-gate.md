# Phase 13E Shadow Classifier Error Review and Paper Radar Release Gate

## Executive Summary

Phase 13D dependencies are complete. The refreshed offline pilot contains 67 repository-grounded records and zero user-confirmed or user-corrected labels. Phase 13E therefore completed an error review without human-gold precision, recall, or F1.

The dominant shadow issue is Track D bucket drift from broad support metadata, followed by complete Track B undercoverage. A field-aware v0.2 rule candidate was prepared under `experiments/`; it is not connected to production and is not claimed to improve accuracy.

## Human-Gold Metric Eligibility

- Annotation rows: 25.
- User-confirmed: 0.
- User-corrected: 0.
- Human-gold metrics eligible: no.
- Error review status: `error_review_complete_without_gold_metrics`.

Production-shadow and Codex-review-shadow comparisons are diagnostic disagreement measures only.

## Shadow Pilot Evidence

- Pilot records: 67.
- Production-shadow agreement: 29.
- Production-shadow disagreement: 38.
- Codex-review-shadow disagreement: 27.
- Reviewed disagreement union: 42.
- Explanation completeness: 100%.
- Strict metadata insufficiency: 0%.

The review script initially exposed a broader-pool parsing defect: five newly available pilot records were absent from the older 62-record static sample file. Pilot predictions now retain their own `available_evidence`, and the review uses that evidence when a static sample row is absent.

## Error Categories

| Primary diagnostic cause | Count | Interpretation |
|---|---:|---|
| `generic_keyword_false_positive` | 17 | Broad support-only terms pulled records toward Track D. |
| `production_label_limitation` | 13 | Shadow and Codex review agreed while the current production label differed. |
| `ambiguous_paper` | 7 | User adjudication is required before rule tuning. |
| `bad_rule` | 3 | Current shadow coverage or precedence was insufficient. |
| `bad_track_definition` | 2 | Secondary/multi-track treatment needs clarification. |

Contributing signals include 21 generic-keyword cases, 20 bad-rule cases, 13 production-label limitations, 7 ambiguous papers, 3 shadow-overreach cases, and 2 track-definition cases. Author-name leakage observed: 0. Insufficient-metadata cases observed: 0.

## Per-Track Review

- Track A: 1 of 5 Codex-reviewed labels matched; generic signature, commitment, and ZK expansion remains prohibited without a central lattice/Module-SIS/chameleon/sanitizable anchor.
- Track B: 0 of 6 matched; technical bridge coverage needs offline revision, with person names forbidden as features.
- Track C: 3 of 10 matched; attack and reduction centrality must outrank incidental scheme mentions, while generic AI/ML/CV remains excluded.
- Track D: all 28 Codex-reviewed Track D rows matched, but shadow selected Track D 50 times, demonstrating bucket drift rather than measured precision.

## Controlled Rule Revision

The v0.2 candidate separates title/abstract primary evidence from taxonomy/keyword support evidence, prevents support-only assignment, applies Track A/B/C central-topic precedence before Track D, and forbids author names and prior labels as features.

Do not promote author-name rules, generic unanchored keywords, support-only assignments, Track D fallback behavior, or any rule tuned against Codex-reviewed labels while presented as human-gold improvement.

## Paper Radar Release Gate

- Paper radar core: `radar_core_stable_with_warnings`.
- Source health and retrieval core: unchanged.
- v0.4.1 release/tag: `blocked_by_multiple_conditions` because durable-run and current remote CI evidence remain separate unresolved gates.
- v0.5 shadow mode: `blocked_until_user_annotation`.
- v0.5 production: `blocked_by_multiple_conditions`.

## ARS Review

`academic-research-suite` was used inline through experiment-agent and academic-paper-reviewer guidance. It reviewed reproducibility, leakage, ambiguity, track boundaries, and overclaiming. It did not assign human-gold labels, retrieve papers, edit production code, or become a runtime dependency.

## Changes Made

- `scripts/run_v0_5_shadow_pilot.py`: retained per-record evidence in self-contained pilot predictions.
- `scripts/review_v0_5_shadow_errors.py`: supported broader-pool records absent from the static sample.
- Focused tests: replaced brittle repository-size constants and added a broader-pool regression.
- Experimental v0.2 rules, review artifacts, gate documents, and reports remain non-production.

## Validation

- Python: 3.15.0b2.
- Workflow doctor: pass; package 0.4.1 and Asia/Singapore are healthy.
- Required focused Phase 13E tests: 10 passed.
- Full repository helper: 510 passed.
- Release hygiene: pass with the documented non-blocking legacy tracked-generated warning.
- `git diff --check`: pass.
- `git diff --cached --check`: pass.
- Remote CI: `TODO_VERIFY`; `gh` is installed but unauthenticated.

## TODO_VERIFY

- User adjudication of priority records.
- Held-out v0.2 evaluation on valid human gold.
- Current Ubuntu and Windows CI after publication.
- Durable Daily artifact persistence and origin/main evidence.
- Separate v0.4.1 release validation before any tag decision.
