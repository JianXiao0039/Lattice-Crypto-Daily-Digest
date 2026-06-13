# Phase 13D ARS Shadow Pilot Review

## Review Mode

Academic Research Suite 0.1.11 was used inline through the `experiment-agent` validation and reproducibility guidance. No full runtime, hooks, agent team, or external reviewer was enabled.

## Evaluation Design Review

- The pilot is deterministic and network-free for fixed repository records and rule JSON.
- The selected annotation pack contains 25 disagreement-prioritized records; the broader candidate pool contains all 62 unique usable repository records.
- The broader pool is not an independent holdout because the experimental rules were designed while inspecting the same repository corpus.
- The disagreement-heavy annotation pack cannot estimate repository prevalence or classifier accuracy.
- Prior annotation explanations are excluded from prediction features, reducing direct label leakage.
- No user-confirmed or user-corrected labels exist, so precision, recall, F1, false-positive rate, and false-negative rate are unavailable as human-gold metrics.

## Reproducibility Review

- Input records retain source provenance.
- Predictions retain production and shadow labels, rule matches, confidence, explanation, and disagreement category.
- Explanation completeness is 100% under the script's structural definition.
- Metadata insufficiency is 0% under the strict definition of missing title plus all evidence fields; this does not mean all abstracts are complete.

## Methodological Risks

1. Track D bucket drift affects 21 Codex-reviewed non-Track-D records.
2. Track B under-coverage affects all 6 Codex-reviewed Track B records.
3. The 43.55% production-shadow agreement rate is diagnostic only, not accuracy.
4. Candidate rules should not be revised against the same corpus without a future held-out or user-labeled evaluation set.

## Recommendation

Continue manual offline shadow analysis and user annotation. Do not enable automatic shadow execution or production integration.
