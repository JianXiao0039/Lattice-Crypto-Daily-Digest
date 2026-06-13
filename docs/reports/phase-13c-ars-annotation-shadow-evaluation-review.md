# Phase 13C ARS Annotation and Shadow Evaluation Review

## Review Mode

`academic-research-suite` was available and used through its default inline `experiment-agent` guidance. Full runtime, agent team, hooks, external cross-model review, and automated repository modification were not enabled.

## Method Review

- Sample bias: the 25-record pack deliberately over-samples disagreements and cannot estimate repository-wide error prevalence.
- Label leakage: prior annotation explanations must not be classifier features. The implementation now uses only retained title, abstract, taxonomy tags, and matched keywords.
- Metric validity: no precision, recall, F1, or accuracy is reported because human-gold count is zero.
- Ambiguity: ambiguous and insufficient-metadata cases remain review states rather than forced track assignments.
- Reproducibility: fixed JSON sample plus fixed experimental rules produces deterministic, network-free outputs.
- Negative controls: generic commitment/signature, generic ML, non-lattice privacy, isogeny, and keyword-collision cases require explicit review coverage.

## Limitations

Track D remains overrepresented in shadow output, Track B is under-covered, and many records lack abstracts. These limitations block claims of improved classification.

## Recommendation

Proceed with the compact user annotation pack and additional offline rule review. Keep all production changes blocked.
