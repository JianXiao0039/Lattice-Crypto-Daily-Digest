# Phase 12E Quick-Paper Artifact Handoff Protocol

生成日期：2026-06-05

本报告属于公开 research tooling protocol。它不包含 target PI email、SoP draft、private application tracker、funding strategy、personal PhD narrative 或 private advisor-specific material。

# Executive Summary

This protocol defines how potentially useful public research-radar findings move from `lattice-crypto-daily-digest` into the concrete quick-paper workspace at `D:\ResearchArtifacts\module-sis-chameleon-hash`.

The protocol exists because the radar repository and artifact repository have different responsibilities. The radar repository discovers, classifies, and records evidence. It should not become the implementation, proof, or paper-construction repository. The artifact workspace consumes only sufficiently actionable findings and turns them into related-work updates, feasibility questions, proof obligations, parameterization tasks, implementation tasks, and comparison dimensions.

The immediate target is:

**A Module-SIS-Based Post-Quantum Chameleon Hash Primitive with Reproducible Parameterization and Implementation**

A high relevance score alone is not sufficient for handoff. A candidate must have a clear lattice/PQC anchor and a concrete intended use. This reduces noise from generic hash, commitment, privacy, AI, blockchain, registration, or standards-background papers that do not help a specific quick-paper section or artifact task.

# Workspace Boundary

| Workspace | Role | Allowed outputs | Forbidden outputs | Git policy | Privacy level |
| --- | --- | --- | --- | --- | --- |
| `D:\Code\CodexProjects\lattice-crypto-daily-digest` | Public paper radar, track synthesis, related-work discovery, TODO_VERIFY manager, handoff packet generator | public reports, track maps, candidate packets, source evidence, exclusion reasoning | construction code, proof claims, private application material, secrets | no automatic add/commit/push/tag; generated artifacts remain uncommitted unless explicitly reviewed | public |
| `D:\ResearchArtifacts\module-sis-chameleon-hash` | Concrete quick-paper artifact workspace | related-work matrix, construction feasibility matrix, proof skeleton, parameterization plan, implementation/tests, comparison table | private PhD application material, unsupported security claims, secrets | no git operation in this phase; later changes require workspace-specific review | public/local research artifact |
| `D:\Code\CodexProjects\PhD_Application` | Private application planning | private narratives, PI notes, SoP drafts, application tracker | public radar outputs presented as private claims; secrets | must not be touched in this phase; never publish by default | private |

# Handoff Eligibility Criteria

## Qualifies for handoff

A candidate qualifies only when it has a clear lattice/PQC anchor and at least one concrete artifact use.

Eligible categories:

- direct Module-SIS / SIS / lattice chameleon hash relevance;
- construction-adjacent relevance:
  - lattice commitment;
  - lattice trapdoor or preimage sampling;
  - lattice-based signature or privacy primitive with transferable construction/proof context;
- parameterization relevance:
  - Module-SIS bounds;
  - estimator inputs;
  - reproducible parameter methodology;
- implementation relevance:
  - reference implementation structure;
  - test methodology;
  - benchmark or reproducibility discipline;
- Xingye Lu public technical bridge relevance:
  - lattice-based linkable ring signatures;
  - hash-then-one-way signatures;
  - programmable hash;
  - post-quantum privacy primitives;
  - only after technical anchor verification;
- comparison relevance:
  - a verified item that supplies a comparison dimension or baseline.

## Does not qualify

- generic hash without lattice/SIS/PQC anchor;
- generic commitment without lattice/SIS/PQC anchor;
- generic privacy, AI, blockchain, registration, ZK, or ring signature without lattice/PQC/HE/FHE anchor;
- high-score paper with no concrete artifact use;
- ML-KEM / ML-DSA background paper unless it supports a concrete section, parameter method, implementation method, or comparison;
- unverified metadata presented as a paper claim;
- any item whose only value is private application planning.

# Handoff Packet Schema

Each handoff packet must contain:

| Field | Meaning | Required rule |
| --- | --- | --- |
| `packet_id` | deterministic public packet identifier | required; suggested form `QPH-YYYY-Www-NN` |
| `source_item_title` | paper or track-item title | required; do not invent |
| `source_file` | public radar file where item was found | required |
| `source_url_or_identifier` | DOI, ePrint, arXiv, or trustworthy URL | empty or `TODO_VERIFY` if unavailable |
| `lattice_pqc_anchor_evidence` | explicit SIS/Module-SIS/lattice/PQC evidence | required |
| `category` | direct, construction-adjacent, parameterization, implementation, bridge, comparison, background | required |
| `why_it_matters` | concise artifact-oriented reason | required; no novelty claim |
| `intended_artifact_use` | exact artifact task | required |
| `possible_paper_section` | introduction, related work, preliminaries, construction, security model, parameterization, implementation, comparison, limitations/future work | required |
| `verified_facts` | facts supported by observed metadata or original source | required; may be minimal |
| `TODO_VERIFY` | unresolved claims and required sources | required |
| `non_claims` | claims explicitly not made | required |
| `recommended_action` | handoff_now, handoff_after_verify, keep_in_radar, backlog, exclude | required |
| `target_artifact_file` | intended file/task in artifact workspace | required for handoff actions |
| `risk_level` | low, medium, high | required |

Full reusable template:

`docs/research_tracks/quick_paper_handoff_packet_template_v0.1.md`

# Handoff Decision Rubric

Score each dimension from 0 to 5. Scores are triage evidence, not ranking replacements and not security judgments.

| Dimension | 0 | 3 | 5 |
| --- | --- | --- | --- |
| direct Module-SIS relevance | none | module-lattice/SIS adjacent | explicitly Module-SIS and useful |
| chameleon hash relevance | none | hash/commitment adjacent with verified anchor | direct chameleon hash construction/security |
| SIS / commitment / trapdoor relevance | none | one adjacent concept | directly supplies an assumption, commitment, or trapdoor mechanism |
| proof usefulness | none | possible vocabulary or model | concrete verified definition/proof obligation |
| parameterization usefulness | none | general parameter background | concrete bounds, estimator inputs, or reproducible method |
| implementation usefulness | none | general engineering lesson | concrete implementation/test/benchmark method |
| comparison table usefulness | none | possible comparison category | verified baseline or comparison dimension |
| Xingye Lu bridge usefulness | none | possible public technical bridge | verified lattice/PQC technical bridge |
| verification burden | low burden | moderate reading needed | high burden or unclear source |
| overclaim risk | low | moderate | high risk of unsupported security/novelty claim |

Decision guidance:

- `handoff_now`: strong direct/actionable value, trustworthy evidence, manageable verification burden, explicit non-claims.
- `handoff_after_verify`: useful but key assumption, source, or construction claim remains unverified.
- `keep_in_radar`: relevant for monitoring but no concrete artifact task yet.
- `backlog`: useful background with low immediate actionability.
- `exclude`: missing hard anchor or no plausible artifact use.

The detailed rubric is stored in:

`docs/research_tracks/quick_paper_handoff_decision_rubric_v0.1.md`

# Non-Claims Policy

A handoff is:

- a structured transfer of possibly useful research material;
- a record of observed evidence and unresolved questions;
- a pointer to an artifact task.

A handoff is not:

- a security proof;
- a novelty claim;
- a claim that a proposed construction works;
- a claim that parameters are secure;
- an implementation or benchmark result;
- a publishable result;
- a verified professor-specific relationship.

The full policy is stored in:

`docs/research_tracks/quick_paper_non_claims_policy_v0.1.md`

# Future Weekly Integration

Future weekly reports should produce five handoff-facing buckets:

1. **Direct handoff candidates**
   - strong anchor;
   - clear artifact use;
   - packet can be created now.
2. **TODO_VERIFY handoff candidates**
   - plausible use;
   - original paper or assumption verification required.
3. **Backlog candidates**
   - useful background;
   - no immediate artifact task.
4. **Excluded noise**
   - generic keyword match or missing lattice/PQC anchor.
5. **Next ChatGPT web reading candidates**
   - items whose verification would unlock a handoff.

Weekly output should be track first and score second. Existing relevance scores remain useful discovery signals but do not determine handoff action.

# Artifact Workspace Intake Plan

`D:\ResearchArtifacts\module-sis-chameleon-hash` should consume packets through explicit artifact tasks:

| Intake destination | Packet use |
| --- | --- |
| related-work queue | add verified candidate, citation task, comparison category, or exclusion note |
| construction feasibility matrix | record possible primitive component, assumption, dependency, and blocker |
| proof skeleton | add definition, security goal, proof obligation, or explicit unresolved reduction question |
| parameterization checklist | add bounds, variables, estimator inputs, or reproducibility source |
| implementation plan | add interface, test, benchmark, or artifact-reproduction task |
| comparison table | add verified comparison dimension, not invented performance data |

Intake rules:

- never silently promote `TODO_VERIFY` to fact;
- keep verified facts separate from background and inference;
- link back to the public packet source;
- state non-claims in artifact notes;
- reject a packet if it cannot name an artifact use.

# Example Handoff Packets

## Example 1: Direct-topic placeholder

```yaml
packet_id: QPH-TODO-01
source_item_title: TODO_VERIFY lattice-based chameleon hash paper
source_file: docs/research_tracks/module_sis_chameleon_hash_todo_verify_queue_v0.1.md
source_url_or_identifier: TODO_VERIFY
lattice_pqc_anchor_evidence: TODO_VERIFY direct lattice/SIS chameleon hash anchor
category: direct
why_it_matters: May provide a direct related-work baseline and security-model comparison.
intended_artifact_use: Add to related-work matrix after original-source verification.
possible_paper_section: Related Work
verified_facts: []
TODO_VERIFY:
  - title
  - authors
  - source
  - assumption
  - construction
non_claims:
  - No novelty or security claim is made.
recommended_action: handoff_after_verify
target_artifact_file: paper/related_work.md
risk_level: high
```

## Example 2: Known public metadata candidate

```yaml
packet_id: QPH-2026-W23-01
source_item_title: Improved Dual Attack and Trapdoor Sampling via Quantum Rejection Sampling
source_file: docs/reports/phase-12c-module-sis-chameleon-hash-related-work-radar.md
source_url_or_identifier: arXiv 2605.24798v1
lattice_pqc_anchor_evidence: Digest metadata contains SIS and trapdoor-sampling context.
category: parameterization
why_it_matters: May provide trapdoor-sampling vocabulary or limitations relevant to feasibility review.
intended_artifact_use: Add a verification task to the construction feasibility matrix.
possible_paper_section: Preliminaries / Limitations
verified_facts:
  - The title and identifier appear in the public weekly metadata.
TODO_VERIFY:
  - original paper scope
  - assumptions
  - relation to Module-SIS chameleon hash
non_claims:
  - This packet does not claim the method supports the proposed construction.
recommended_action: handoff_after_verify
target_artifact_file: research_radar/todo_verify_literature_queue.md
risk_level: medium
```

## Example 3: Background-only candidate

```yaml
packet_id: QPH-2026-W23-02
source_item_title: On the Secrecy of the Encapsulation Coin in ML-KEM
source_file: docs/reports/phase-12c-module-sis-chameleon-hash-related-work-radar.md
source_url_or_identifier: IACR ePrint 2026/1117
lattice_pqc_anchor_evidence: Explicit ML-KEM anchor.
category: background
why_it_matters: Supports general PQC maturity but has no current concrete Module-SIS artifact use.
intended_artifact_use: None unless a reproducibility method transfers.
possible_paper_section: None
verified_facts:
  - Public radar metadata identifies the title and ePrint ID.
TODO_VERIFY:
  - whether any method transfers to parameterization or implementation discipline
non_claims:
  - This is not direct Module-SIS chameleon hash support.
recommended_action: keep_in_radar
target_artifact_file: none
risk_level: low
```

# Recommended Future Phases

- **RA-2: Construction Feasibility Matrix**
  - map candidate components, assumptions, interfaces, proof obligations, and blockers.
- **RA-3: Parameterization and Implementation Plan**
  - define variables, estimator inputs, toy parameters, tests, and reproducibility scope.
- **RA-4: Proof Skeleton and Security Claim Boundary**
  - separate definitions, proof obligations, proof sketches, unsupported claims, and limitations.
- **Phase 12F: Track-Based Weekly Handoff Implementation Plan**
  - design a future implementation plan without changing ranking thresholds.

# TODO_VERIFY

- Whether future weekly synthesis can generate packet drafts without changing ranking semantics.
- Whether current JSON records contain enough stable identifiers, anchor evidence, and source provenance.
- Whether packet generation requires code changes or can remain documentation-driven.
- Whether public packet drafts should be committed or only mirrored locally after review.
- Whether related work should always be read in ChatGPT web before `handoff_now`.
- Whether artifact workspace intake should use one queue file or per-packet files.
- Whether the decision rubric needs track-specific thresholds after manual pilot use.

