# Phase 13B: v0.5 Gold Sample Expansion and Offline Track Precision Evaluation

## Executive Summary

`$academic-research-suite` version `0.1.11` was available and used inline. Experiment-agent produced the evaluation protocol; academic-paper-reviewer audited labels, leakage, balance, and interpretation. Full runtime, agent teams, hooks, and external cross-model review remained disabled.

The existing 15-record provisional sample was audited and expanded to all 62 unique usable repository records. All 15 original identifiers were retained. No existing annotation was treated as human verified. Every v0.2 row is `needs_user_review`; human-gold count is zero.

The minimum sample gate of 60 is met, but the target of 80 and recommended per-track balance are not. Offline design gate: `sample_design_ready_with_coverage_gaps`. Production gate: `blocked_by_multiple_conditions`.

## Scope and Production Freeze

This phase added an isolated experimental evaluator and documentation only. It did not change production taxonomy, ranking, queries, negative keywords, section classification, source fetchers, relevance scoring, workflow scheduling, package version, or production track assignment.

Repository JSON records were the only paper source. No papers or metadata were invented, and no external paper lookup was used.

## Sample Expansion

| Item | Result |
|---|---:|
| Original provisional records | 15 |
| Original identifiers retained | 15 |
| Expanded repository-grounded records | 62 |
| Target | 80 |
| Minimum acceptable | 60 |
| Records with retained abstracts | 55 |
| Records without retained abstracts | 7 |
| Human-confirmed/corrected records | 0 |
| Records needing user review | 62 |

## Sample Distribution

| Reviewed provisional label | Count |
|---|---:|
| `module_sis_sanitizable_signatures` | 4 |
| `xingye_lu_bridge` | 6 |
| `ai4lattice_cryptanalysis` | 9 |
| `core_pqc_and_implementation` | 25 |
| `irrelevant` | 11 |
| `ambiguous` | 7 |

Coverage gaps:

- total sample is 18 below target;
- Tracks A, B, and C are below the recommended 16 each;
- ambiguous coverage is 7 rather than 8;
- Track D is overrepresented and requires internal error analysis;
- Track A lacks a sufficient direct chameleon-hash/sanitizable-signature corpus.

## Annotation Separation

Each row contains separate machine, Codex-review, and human-gold fields. Only `user_confirmed` and `user_corrected` rows may count as final gold. Current annotation coverage is 0.000.

The v0.1 file called itself a gold sample, but its 15 records had no human-review status. Phase 13B therefore treats all 15 as provisional historical annotations.

## Offline Metrics

Human-gold precision, recall, F1, macro metrics, and micro F1 are `N/A` because valid gold count is zero.

Machine-to-Codex diagnostics are reported only for rule debugging:

| Metric | Diagnostic value |
|---|---:|
| Macro precision | 0.680 |
| Macro recall | 0.873 |
| Macro F1 | 0.728 |
| Micro F1 | 0.698 |
| Irrelevant false-positive rate | 0.545 |
| Ambiguous coverage | 0.857 |
| No-label rate | 0.097 |
| Multi-track disagreement rate | 0.833 |
| Explanation completeness | 1.000 |
| Human annotation coverage | 0.000 |

These values do not measure production quality. Machine proposals and Codex provisional labels share the same repository evidence and are not independent.

## False-Positive Review

Main provisional categories:

1. Track D absorbs generic implementation/FHE/PQC vocabulary.
2. Track B reacts to generic privacy and anonymity language.
3. Track A reacts to generic commitment or trapdoor terms without sufficient Module-SIS/chameleon/sanitization evidence.
4. Scheme-name collisions and non-lattice PQC require explicit exclusion evidence.

The machine-to-Codex table contains 34 provisional false-positive track assignments. This count is diagnostic, not a human-gold error count.

## False-Negative Review

Five provisional false-negative track assignments were observed. Four involve Track C, showing that classical BKZ/reduction/attack baselines can be missed when attack evidence does not use the script's narrow phrases. One involves Track B.

The Track C result supports an explicit future distinction between classical attack baselines and learning-guided attacks.

## Ambiguous and Multi-Track Cases

Seven records remain ambiguous because lattice/PQC anchoring or technical centrality is not established strongly enough by retained metadata. Six records have provisional secondary tracks. These cases are prioritized in the annotation queue.

No Track B row is evidence of Xingye Lu authorship, affiliation, recruitment, or personal fit. The label means possible technical bridge only.

## Explanation Quality

All 62 rows contain positive evidence, exclusion evidence, an explanation, and provenance, producing structural completeness of 1.000. This does not establish factual correctness, paper-level claim verification, or human agreement.

## Offline Rule Candidates

Candidate rules are documented for future shadow-mode design only:

- hard lattice/PQC anchoring before generic commitment/signature/privacy/AI terms can assign a track;
- ambiguous treatment for ring/linkable signatures without lattice evidence;
- explicit scheme-name collision filtering;
- preservation of classical lattice attacks as Track C baselines;
- tighter Track D boundaries for generic FHE and broad PQC applications.

No candidate was promoted into production.

## Gates

Offline design gate: `sample_design_ready_with_coverage_gaps`.

Production gate: `blocked_by_multiple_conditions` due to:

- zero human-gold labels;
- unavailable human-gold metrics and metric target;
- incomplete sample balance;
- current CI recovery still pending outside this phase;
- durable post-tag Daily evidence still absent.

The next permitted step is user annotation and later shadow-mode planning, not production implementation.

## Files and Reproducibility

Run:

```text
python scripts/evaluate_v0_5_track_precision.py
```

The evaluator reads existing daily/weekly JSON, writes only experimental docs/reports, and is deterministic for fixed inputs and code.

## Validation Results

| Check | Result |
|---|---|
| Python | `3.15.0b2` |
| Active package | `0.4.1` |
| Environment imports and `Asia/Singapore` | passed |
| Workflow doctor | passed |
| Experimental evaluator | exit 0; 62 records generated |
| Focused evaluator tests | 7 passed |
| Repository test helper | 478 passed |
| Release hygiene | passed; existing legacy tracked-generated warning remains non-blocking |

`git diff --check` and final `git status -sb` are recorded after the final documentation update.

## TODO_VERIFY

- user adjudication of all 62 records;
- direct Track A corpus growth through normal repository ingestion;
- Track B scope acceptance by the user;
- Track C classical-versus-learning subtype design;
- Track D subdivision for evaluation analysis;
- human-gold metric targets;
- future shadow-mode rules after CI and durable-run recovery.
