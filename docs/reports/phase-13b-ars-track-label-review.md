# Phase 13B ARS Track Label Review

## Material Passport

- Origin skill: `academic-research-suite`
- Workflow: `academic-paper-reviewer`
- Review mode: methodology/domain/devil's-advocate synthesis
- Adapter version: `0.1.11`
- Date: `2026-06-12`
- Verification status: `ANALYZED`
- Reviewed artifacts: track definitions, v0.2 sample, coverage report, offline metrics, error tables, and production gate
- External cross-model review: not used

## Methodology Review

### Strengths

1. Machine proposals, Codex-reviewed labels, and human-gold fields are structurally separate.
2. All 15 v0.1 records are retained, but none is silently promoted to human gold.
3. All 62 records are grounded in repository JSON and retain source provenance.
4. Human-gold precision, recall, and F1 are correctly withheld because valid gold count is zero.
5. The evaluator is isolated under `scripts/` and does not invoke or change production classification.

### Methodological Limitations

1. Machine proposals and Codex review use the same retained title, abstract, taxonomy, and keyword evidence. Their comparison is not an independent validation and is vulnerable to shared-evidence leakage.
2. The sample is a census of available repository records, not a balanced random or stratified sample. Reported diagnostics cannot estimate deployment prevalence.
3. The sample reaches the minimum 60-record gate but not the 80-record target. Track A, Track B, Track C, and ambiguous strata remain below recommended coverage.
4. Seven records lack retained abstracts. Title and taxonomy evidence may be insufficient for final adjudication.
5. Explanation completeness is a structural-field metric. A value of 1.000 does not demonstrate explanation correctness or usefulness.

## Domain Label Review

### Track A: Module-SIS / Sanitizable Signatures

Coverage is inadequate. Four primary candidates and two secondary candidates do not provide a representative sample of chameleon hashing, sanitizable signatures, exposure models, accountable sanitization, commitments, and trapdoors. Several candidates are construction-adjacent rather than direct target papers.

Required interpretation: Track A rules are not ready for metric targets or production tuning.

### Track B: Xingye Lu Bridge

The label is technical, not biographical. No row may imply Xingye Lu authorship, affiliation, recruitment, or personal fit.

The six primary candidates cover lattice blind signatures and lattice privacy protocols, but ABE, PIR, traitor tracing, message franking, and PRE are broader than ring/linkable/hash-then-one-way signatures. Human review must decide whether these are useful bridge papers or overly broad privacy primitives.

Required interpretation: technical adjacency is provisional and must not be reported as a fact about a person.

### Track C: AI4Lattice Cryptanalysis

No generic machine-learning paper is included as a positive Track C item. Classical BKZ, reduction, dual attack, sparse-secret, and estimator papers are retained as attack baselines, which matches the stated longline scope.

Risk: the track name can imply AI usage where none exists. Reports must distinguish `classical_attack_baseline` from `learning_guided_attack` during future annotation.

### Track D: Core PQC and Implementation

Track D contains 25 primary records and is the largest stratum. It mixes ML-KEM/ML-DSA, NTRU, HAWK, FHE algorithms, FHE applications, hardware acceleration, protocol integration, and fault analysis.

Risk: Track D can become a miscellaneous bucket. Human review should distinguish concrete standardized-PQC support from generic FHE applications and broad post-quantum deployment papers.

## Devil's Advocate Findings

### Major: Diagnostic Metrics Could Be Misread as Precision

The strongest counterargument to any performance claim is the absence of user-confirmed labels. A macro F1 computed against Codex provisional labels measures consistency with the same review process, not correctness. It must remain under a heading explicitly marked `not gold`.

### Major: Track Balance Can Distort Rule Conclusions

Track D's large share and Track A's small share mean aggregate metrics can improve while the short-term Module-SIS research target remains poorly served. Macro metrics do not repair missing subtopic coverage.

### Major: Generic Terms Still Create False Positives

The provisional machine proposer has high false-positive pressure from generic implementation, privacy, signature, and commitment terms. The observed irrelevant false-positive rate of 0.545 is a debugging signal, not a permanent estimate, but it confirms that hard lattice/PQC anchoring is necessary.

### Moderate: False Negatives Concentrate in Classical Attack Baselines

Track C false negatives show that attack relevance cannot depend on AI vocabulary. Classical lattice reduction and attack-interface papers are necessary controls for AI4Lattice evaluation.

### Moderate: Multi-Track Explanations Need Human Adjudication

The multi-track disagreement rate is high in the provisional comparison. Secondary-track assignments should not be promoted until the user confirms the intended handoff use.

## Editorial Synthesis

### Label Review Decision

`major_revision_required_before_gold_evaluation`

The sample structure and experimental evaluator are suitable for offline annotation work, with explicit coverage gaps. They are not sufficient for production rule changes.

### Accepted Claims

- 62 repository-grounded records were assembled.
- all 15 v0.1 records were retained and marked for user review;
- no human-gold metrics are available;
- machine-to-Codex diagnostics reveal rule-design failure modes;
- sample design is ready with coverage gaps;
- production remains blocked.

### Claims to Avoid

- the evaluator has measured production precision or recall;
- the labels are gold;
- Track B demonstrates facts about Xingye Lu;
- Track C records all use machine learning;
- Track D is a coherent single technical category without further review;
- the sample is balanced or representative of the external literature.

## Required Follow-Up

1. User-adjudicate ambiguous, multi-track, and Track A/B records first.
2. Add direct Module-SIS chameleon-hash and sanitizable-signature records only when they enter the repository through approved public research workflows.
3. Add a Track C evidence subtype separating classical baselines from learning-guided methods in the annotation schema before production use.
4. Split Track D analytically during review, without changing production taxonomy in Phase 13B.
5. Define metric targets only after a sufficiently broad human-gold subset exists.

