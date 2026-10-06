# Evidence-bounded relevance and synthesis V2

Baseline: published stabilization `bf684e4fda130051696a4de47632b86aa7804172`.

## One-way interpretation

Original source title, abstract and source conclusion establish evidence. Translated
titles, generated conclusions, summaries, rationales, recommendation tags and legacy
taxonomy are presentation/provenance fields. None is an extraction input.

`SOURCE_EXPLICIT`, `SOURCE_STRUCTURAL` and `SOURCE_RELATION` describe source-grounded
material. `MODEL_INFERENCE`, `USER_RESEARCH_HYPOTHESIS` and `GENERATED_PROSE` cannot
be promoted into those classes. Source mentions are not automatically claims of
an attack, improvement, construction or proof. Concept occurrence edges use
`MENTIONS`; specialized relations require their own source grammar/coanchors.
This deterministic interpretation does not verify the paper's proof or establish
a standardized cryptosystem break.

Machine fields separate `source_taxonomy_tags`, `source_evidence_terms`, and
`source_concept_ids` from `inferred_topic_tags`, `ontology_neighbor_tags`, and
`user_research_hypotheses`. A hypothesis carries
`RESEARCH_HYPOTHESIS_NOT_PAPER_CLAIM`. The renderer prints only source-supported
DIRECT/STRUCTURAL relations, and explicitly labels INDIRECT hypotheses.

## Scope and scoring

`DIRECT_LATTICE_CRYPTO` requires a source lattice assumption, construction,
scheme or security target. `DIRECT_LATTICE_HARDNESS_THEORY` covers source-supported
lattice problems/reduction algorithms with foundational cryptographic relevance.
Generic method vocabulary and non-cryptographic lattice applications do not
establish either scope. `LATTICE_METHOD_IN_ADJACENT_CRYPTO` and `ADJACENT_PQC`
are capped at C (59). `INDIRECT_RESEARCH_HYPOTHESIS` is distinct from a paper claim;
`OUT_OF_SCOPE` is capped at D (39).

`score_to_label` is the final mapping: 80–100 A, 60–79 B, 40–59 C, 0–39 D.
Scope caps constrain the score before assigning its label. The semantic verifier
rejects inconsistent pairs, including legacy B/80. Title-only evidence is weaker
than an abstract. Source-supported critical claims retain their dedicated
verification urgency; CRITICAL is a claim requiring verification, not a proof.

Ontology evidence policies apply to original source text. Generic physical attacks
need a lattice target. Generic lattice methods need a qualified lattice anchor.
Neighbors and generated tags never satisfy coanchors. Grammatical plurals retain
the same concept; the existing SIS acronym now has an explicit guarded source
entry instead of relying on its inferred alias. Epidemiological SIS is excluded.
Negative applicability statements constrain targets and remain visible as source
limitations. Negative security conditions such as absence of a trusted setup do
not discard the paper's genuine contribution.

## Recommendations and provenance

`research_value_score` is a deterministic source-grounded research triage score,
independent of recency, venue confidence and source health. It is not a measured
scientific impact factor. `freshness_urgency` governs current-window reading;
`verification_urgency` governs claim/source/date checks. `recommended_action` and
the compatible `suggested_action` may request reading today without making the
scientific recommendation Strong. `recommendation_score` remains the compatible
risk/freshness-capped triage value and never exceeds intrinsic research value.
There is no fresh-primary/strong-axis floor of 85 or 65.

Selected records carry `source_health` and per-source
`source_health_provenance`. New observations override older observations for the
same source; absent observations preserve existing provenance. Merged sources
remain separate, with the aggregate reflecting the worst observed health.
Unknown health is explicit rather than an empty string.

## Period synthesis and independent quality

Historical Daily rows remain unchanged. Period reports expose
`provenance_label_counts`, `validated_label_counts`, `classification_conflicts`,
`classification_conflict_count`, and `classification_quality_state`. Historical
record scores/recommendations are explicitly upstream/provenance values. Daily
themes and period research interpretation use original source evidence only.

Coverage integrity and classification quality are independent: period input
assessment checks durable publication semantics separately from the relevance
verifier. Missing/invalid expected days or semantic UNKNOWN produce
`INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS`; preserved semantic FAIL evidence may
produce `PARTIAL_VERIFY_FIRST`. Fully present, semantic-PASS source-degraded days
produce `AUTHORITATIVE_DEGRADED`; fully valid days produce
`AUTHORITATIVE_COMPLETE`. Classification conflicts do not impersonate coverage
degradation. Source roles determine required discovery coverage; enrichment-only
failures stay visible without becoming missing required discovery sources.

## Quality gates and benchmark provenance

The semantic verifier and machine report enforce score/label consistency (100%)
and zero inference feedback, generated prose extraction, ontology coanchor
violations, unsupported direct relations, missing selected health provenance, and
missing-period false degradation. Existing freshness, duplicate, critical and
unsafe-merge tests remain collected.

Benchmark V2 retains all 200 records and original labels/source snapshots.
Evidence-supported corrections use its existing adjudication overlay, with an
explicit audit rationale. They are Codex source audits, not human adjudications.
Both original-gold and overlay metrics must remain in external validation evidence;
no threshold is lowered and no old test is removed to obtain a pass.

Historical replays and validation outputs belong in an external candidate. This
phase does not regenerate canonical Daily/Weekly/Monthly artifacts, activate Query
Portfolio V3, enable a translation backend, alter automations, or push the local
integration commit.
