# Reproducibility Plan

Selected paper: Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE

## 2-Hour Artifact

- Goal: create a verified metadata and reading card.
- Required inputs: ePrint page, abstract, introduction.
- Expected outputs: title, authors, problem statement, contribution summary, first TODO_VERIFY list.
- Validation method: every metadata field matches original source.
- Risk: insufficient technical depth.
- TODO_VERIFY: main claim and exact attack model.

## 1-Day Artifact

- Goal: extract definitions, parameters, and score/covariance objects.
- Required inputs: full paper PDF, Phase 11B notes.
- Expected outputs: parameter table, symbol table, claim table.
- Validation method: each row includes section/page reference.
- Risk: formulas may require background references.
- TODO_VERIFY: whether parameters are close to MLWE / ML-KEM.

## 1-Week Artifact

- Goal: produce a public reproducibility planning note for LWE dual-attack analysis.
- Required inputs: original paper, related dual attack papers, estimator background.
- Expected outputs: assumptions table, parameter checklist, possible toy reproduction design.
- Validation method: no experiment claim without script/log; no security claim without paper support.
- Risk: paper may not include reproducible code or enough numeric details.
- TODO_VERIFY: toy parameter validity.

## 1-Month Artifact

- Goal: design a bounded AI4Lattice baseline map around score-distribution signals.
- Required inputs: extracted definitions, toy LWE generator, classical baseline references, manual review.
- Expected outputs: candidate feature/label table, toy benchmark plan, limitations statement.
- Validation method: compare with classical baseline; state toy-to-real limitations.
- Risk: overclaiming AI usefulness.
- TODO_VERIFY: whether score/covariance quantities are valid ML labels or features.

## Stop Conditions

Stop or downgrade the artifact if:

- the paper does not provide enough parameter detail;
- the score definition is too paper-specific to reuse;
- MLWE / ML-KEM relevance is not present;
- reproduction requires unsafe or unavailable implementation details;
- the artifact risks overstating practical security impact.
