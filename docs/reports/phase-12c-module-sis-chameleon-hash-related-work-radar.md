# Phase 12C Module-SIS Chameleon Hash Related Work Radar

生成日期：2026-06-04

本报告属于公开 research radar / track-synthesis 工作流。它不包含 target PI email、SoP draft、PI-specific application note、funding strategy、personal PhD application tracker、personal PhD narrative 或 private application material。

# Executive Summary

This radar exists to turn the public lattice/PQC digest stream into a focused related-work queue for the short-term small-paper artifact:

**A Module-SIS-Based Post-Quantum Chameleon Hash Primitive with Reproducible Parameterization and Implementation**

It differs from single-paper deep reading:

- it does not deep-read one selected paper;
- it classifies multiple candidates by usefulness to the small-paper track;
- it prioritizes actionability over generic A-score relevance;
- it creates a handoff to `D:\ResearchArtifacts\module-sis-chameleon-hash`.

Main result:

- No recent W23 item is verified as a direct Module-SIS chameleon hash construction.
- Several candidates are construction-adjacent or background-useful, especially `BRaccoon`, `Witness Pseudorandom Functions for Vector Commitments and Applications`, `Improved Dual Attack and Trapdoor Sampling via Quantum Rejection Sampling`, and `Module Lattice Security (Part IV)`.
- The immediate related-work gap remains: verified lattice-based chameleon hash papers and SIS / Module-SIS commitment papers.

# Input Evidence Used

| Input | Status | How used | Limitation |
| --- | --- | --- | --- |
| `docs/reports/phase-12a-module-sis-chameleon-hash-track-calibration.md` | available | Strategy and track definition | Documentation only; no code behavior changed |
| `docs/reports/phase-12b-track-based-weekly-report-template.md` | available | Weekly track template and action categories | Template only |
| `docs/research_tracks/module_sis_chameleon_hash_track.md` | available | Inclusion/exclusion criteria | Requires future code/template implementation |
| `docs/research_tracks/xingye_lu_bridge_track.md` | available | Public technical bridge policy | No private PI material included |
| `docs/research_tracks/track_keywords_v0.1.md` | available | Keyword recommendations | Not code taxonomy |
| `docs/research_tracks/negative_keyword_policy_v0.1.md` | available | Generic-keyword exclusion rule | Not code enforcement yet |
| `docs/research_tracks/weekly_report_template_v0.1.md` | available | Weekly output design | Template only |
| `docs/research_tracks/weekly_track_scoring_rubric_v0.1.md` | available | Actionability rubric | Triage only |
| `data/weekly/2026-W23.json` | available | Candidate extraction from recent records | Generated metadata; original papers not read |
| `digests/weekly/2026-W23.md` | available | Weekly context | Generated narrative |
| `D:\ResearchArtifacts\module-sis-chameleon-hash\README.md` | available | Artifact project goal and roadmap | Handoff only; no code modified |
| `D:\ResearchArtifacts\module-sis-chameleon-hash\paper\related_work.md` | available | Existing related-work buckets | File not modified in this phase |

# Track Definition

## Purpose

Find papers, notes, and track items that support:

- Module-SIS chameleon hash definition;
- trapdoor collision / adaptation mechanism;
- lattice commitment related work;
- SIS / Module-SIS assumption mapping;
- parameter estimation;
- reproducible implementation.

## Inclusion criteria

Include only if there is a clear lattice/PQC anchor:

- SIS / Module-SIS / MSIS;
- lattice commitment;
- lattice-based chameleon hash;
- lattice trapdoor or trapdoor sampling;
- lattice signature or ring signature with proof techniques relevant to primitive design;
- post-quantum primitive using lattice assumptions.

## Exclusion criteria

Exclude:

- generic hash;
- generic commitment;
- generic ring signature;
- generic privacy;
- generic registration;
- generic AI / LLM / optimization;
- generic blockchain;
- generic ZK;
- non-cryptographic lattice.

## Immediate relevance categories

- Directly Relevant
- Construction-Adjacent
- Parameterization / Implementation Support
- Xingye Lu Bridge Candidates
- Background Only
- Exclude / Noise

## TODO_VERIFY policy

Every candidate remains TODO_VERIFY until the original paper confirms:

- assumption;
- construction type;
- trapdoor mechanism;
- parameter relevance;
- relation to chameleon hash / commitment / signature.

# Related Work Radar Categories

## 1. Directly Relevant

Current W23 evidence: no verified direct Module-SIS chameleon hash construction found.

Need future search:

- `Module-SIS chameleon hash`
- `SIS chameleon hash`
- `lattice-based chameleon hash`
- `lattice trapdoor collision`

## 2. Construction-Adjacent

Candidate types:

- lattice-based signatures;
- blind lattice signatures;
- vector commitments;
- lattice-based PRE / ABE / IBE;
- trapdoor sampling;
- programmable hash;
- hash-then-one-way signatures if lattice/PQC anchored.

## 3. Parameterization / Implementation Support

Candidate types:

- Module-LWE / Module-SIS security papers;
- lattice estimator / parameter papers;
- rejection sampling / trapdoor sampling papers;
- reproducible PQC implementation papers.

## 4. Xingye Lu Bridge Candidates

Public technical bridge only:

- lattice-based linkable ring signatures;
- ring-signature / anonymous-authentication technical literature;
- programmable hash / hash-then-one-way signature line;
- post-quantum privacy primitives.

Do not include professor-specific claims, emails, application strategy, or private material.

## 5. Background Only

MLWE / ML-KEM / ML-DSA papers are useful for maturity and standards background but should not dominate the quick-paper track unless they support parameterization or lattice primitive design.

## 6. Exclude / Noise

Generic privacy / GBDT / FHE application papers should stay watchlist unless original reading confirms a lattice/PQC/HE/FHE construction anchor.

# Candidate Table

| Candidate title / item | Source file | Source / ID | Category | Lattice/PQC anchor evidence | Why it may help the small paper | Possible usage in paper | Verification status | TODO_VERIFY | Recommended action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BRaccoon: Concurrently Secure Blind Lattice Signatures from Raccoon | `data/weekly/2026-W23.json` | IACR ePrint 2026/1084 | Construction-Adjacent | digest tags include ML-DSA, Commitments; section includes Lattice Advanced Primitives | may provide lattice signature / privacy primitive context | related work for lattice signatures and commitment-adjacent primitives | metadata only | verify assumptions, security model, whether SIS / Module-SIS appears | skim |
| Witness Pseudorandom Functions for Vector Commitments and Applications | `data/weekly/2026-W23.json` | IACR ePrint 2026/1079 | Construction-Adjacent | digest tags include LWE, SIS, Commitments | may inform commitment vocabulary and proof goals | background for commitment-related section | metadata only | verify whether construction is lattice-based and useful for chameleon hash | skim |
| Improved Dual Attack and Trapdoor Sampling via Quantum Rejection Sampling | `data/weekly/2026-W23.json` | arXiv 2605.24798v1 | Parameterization / Implementation Support | digest tags include SIS, Cryptanalysis, FHE, PQC Implementation; title has trapdoor sampling | may support trapdoor/sampling background | proof-background / trapdoor sampling notes | metadata only | verify trapdoor model and relation to SIS/Module-SIS | read_now |
| Module Lattice Security (Part IV): Probabilistic Polynomial Quantum Attack on Module-LWE over 2-Power Cyclotomics | `data/weekly/2026-W23.json` | arXiv 2605.17412v2 | Parameterization / Background | digest tags include MLWE, Module-SIS, ML-KEM | may inform module-lattice security caution | background for parameter/security section | metadata only | verify claim scope and whether Module-SIS tag is real | watch |
| HRA-Secure Lattice-based Proxy Re-Encryption without Noise Flooding | `data/weekly/2026-W23.json` | IACR ePrint 2026/1113 | Construction-Adjacent | lattice-based PRE, LWE, BGV metadata | may offer lattice primitive proof or noise-management background | related-work only unless assumptions transfer | metadata only | verify construction assumptions and noise flooding relevance | backlog |
| Ciphertext-Updatable Attribute-Based and Predicate Encryption from Lattices | `data/weekly/2026-W23.json` | IACR ePrint 2026/1045 | Construction-Adjacent | "from Lattices"; digest tags LWE/SIS | may inform lattice advanced primitive landscape | related work for lattice primitive context | metadata only | verify assumptions and whether useful beyond background | backlog |
| Identity-Based Revocable and Linkable Ring Signature | `data/weekly/2026-W23.json` | IACR ePrint 2026/1111 | Xingye Lu Bridge Candidate / Watch | linkable ring signature title; lattice/PQC anchor not verified | possible bridge if lattice/PQC anchored | watchlist only | metadata suggests low relevance | verify whether non-lattice; exclude if no lattice/PQC anchor | watch |
| KAT-Seeded Fuzzing of Stateful Hash-Based Signature Verification in liboqs | `data/weekly/2026-W23.json` | IACR ePrint 2026/1107 | Background Only | liboqs / PQC implementation metadata | could support reproducibility discipline | implementation background only | metadata only | not Module-SIS related unless signature scheme is lattice/PQC relevant | watch |
| On the Secrecy of the Encapsulation Coin in ML-KEM | `data/weekly/2026-W23.json` | IACR ePrint 2026/1117 | Background Only | ML-KEM / FIPS 203 / randomness | supports PQC maturity but not quick-paper core | background for standards/security review | original page/PDF accessible from Phase 11D | avoid overusing for Module-SIS chameleon hash | backlog |
| Practical Anonymous Two-Party Gradient Boosting Decision Tree | `data/weekly/2026-W23.json` | arXiv 2605.26903v1 | Exclude / Noise | digest tags suggest FHE, but title is generic privacy ML | weak small-paper relevance | none unless FHE/lattice verified | metadata only | verify real FHE/HE anchor before watchlist | exclude |

# Gap Analysis for Small Paper

Missing related-work needs:

- classical chameleon hash foundation;
- lattice-based chameleon hash constructions;
- SIS / Module-SIS commitment papers;
- trapdoor collision mechanism references;
- lattice trapdoor / preimage sampling references;
- parameter estimation guidance for Module-SIS;
- implementation baseline for keygen/hash/adapt/verify;
- security model comparison;
- comparison table against classic and lattice chameleon hash variants;
- reproducibility artifact convention.

# Query and Keyword Recommendations

Future search terms:

- `Module-SIS chameleon hash`
- `SIS chameleon hash`
- `lattice-based chameleon hash`
- `lattice trapdoor collision`
- `SIS commitment`
- `Module-SIS commitment`
- `programmable hash lattice`
- `lattice-based linkable ring signature`
- `hash-then-one-way signature lattice`
- `lattice trapdoor function`
- `GPV trapdoor chameleon hash`

Negative rules:

- reject generic `hash` without lattice/SIS/PQC anchor;
- reject generic `commitment` without lattice/SIS/PQC anchor;
- reject generic `registration` without lattice/PQC anchor;
- reject generic `AI` without lattice cryptanalysis anchor;
- reject generic `ring signature` unless lattice/PQC/post-quantum relation is verified.

# Handoff to ResearchArtifacts

Target:

`D:\ResearchArtifacts\module-sis-chameleon-hash`

Created handoff files:

- `research_radar/phase-12c-related-work-handoff.md`
- `research_radar/todo_verify_literature_queue.md`

Handoff includes:

- related work queue;
- TODO_VERIFY queue;
- suggested small-paper sections;
- what to read in ChatGPT web;
- what to implement later;
- what not to overclaim.

# Impact on Future Weekly Reports

Weekly Public Synthesis should change:

- track first, score second;
- actionability over generic high score;
- related-work usefulness over novelty hype;
- no automatic deep reading pack by default;
- direct Module-SIS support should be separated from ML-KEM / AI4Lattice background.

# Next Phases

- Phase 12D: Xingye Lu Bridge Literature Map.
- Phase RA-1: Module-SIS Chameleon Hash Artifact Skeleton.
- Phase RA-2: Construction Feasibility Matrix.
- Phase RA-3: Parameterization and Implementation Plan.

# TODO_VERIFY

- No direct Module-SIS chameleon hash paper was found in recent W23 candidates.
- W23 section labels sometimes over-broaden SIS / commitment relevance.
- Every candidate above needs original-paper verification before it enters `paper/related_work.md`.
- ResearchArtifacts related-work file was read but not modified.
- Future code changes may be needed for track labels, but this phase made no code changes.

# Boundary Statement

No source ingestion, ranking thresholds, taxonomy semantics, section classifier, query expansion, negative keyword semantics, workflow semantics, release metadata, generated digest artifacts, `papers.db`, `.env`, secrets, or `PhD_Application` files were modified.
