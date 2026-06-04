# Phase 12B Track-Based Weekly Report Template

生成日期：2026-06-04

本报告属于公开 lattice/PQC research tooling track。它不包含 target PI emails、SoP drafts、PI-specific application notes、funding strategy、personal PhD application tracker content、personal PhD narrative 或 private application materials。

# Executive Summary

Weekly reports are being redesigned because the repository is more useful as a lattice/PQC research radar and idea-support tool than as a default single-paper deep-reading generator. Single-paper reading is still useful, but the user usually handles it in ChatGPT web, where interactive reading is more natural.

Track-based weekly synthesis better serves the short-term paper goal by separating:

- papers directly useful for Module-SIS chameleon hash;
- technical bridge papers for linkable signatures / programmable hash / lattice privacy;
- MLWE / ML-KEM / ML-DSA background assets;
- AI4Lattice longline watchlist items;
- generic noise that should not be escalated.

This design helps the Module-SIS chameleon hash track by prioritizing papers that can support definition, assumptions, proof sketch, parameterization, and implementation. It helps the Xingye Lu technical bridge work by tracking public technical literature around lattice signatures, linkable signatures, and post-quantum privacy primitives without creating private application materials.

# Input Evidence Used

| Input | Status | How used | Limitation |
| --- | --- | --- | --- |
| `docs/reports/phase-12a-module-sis-chameleon-hash-track-calibration.md` | available | Source of strategy shift and future phase plan | Strategy doc only; no code behavior changed |
| `docs/research_tracks/module_sis_chameleon_hash_track.md` | available | Defines primary short-term track | Requires future implementation review |
| `docs/research_tracks/xingye_lu_bridge_track.md` | available | Defines public technical bridge boundaries | Must not become private PI matching |
| `docs/research_tracks/ai4lattice_longline_track.md` | available | Defines long-term AI4Lattice watchlist | Requires hard anti-hype guard |
| `docs/research_tracks/mlkem_mldsa_background_track.md` | available | Defines PQC background escalation criteria | Background track should not dominate quick-paper focus |
| `docs/research_tracks/track_keywords_v0.1.md` | available | Used for track keywords | Not code taxonomy |
| `docs/research_tracks/negative_keyword_policy_v0.1.md` | available | Used for exclusion policy | Not enforced in code yet |
| latest weekly/daily artifacts | available in repository | Used only as examples of prior report style | No generated digest artifacts modified |

# New Weekly Report Design

Future weekly reports should use these sections:

1. Executive Summary
2. Directly Useful for Module-SIS Chameleon Hash
3. Useful for Xingye Lu Technical Bridge
4. MLWE / ML-KEM / ML-DSA Background Assets
5. AI4Lattice Longline Watchlist
6. Lattice/PQC Privacy and Registration-Based Encryption Watchlist
7. Excluded Generic / Noise Papers
8. TODO_VERIFY Queue
9. Next 3 Papers to Read in ChatGPT Web
10. Idea Backlog Updates
11. One-Week Action Plan

The key output is not "one paper to deep-read automatically." The key output is a track-based decision surface: read, skim, backlog, watch, exclude, or TODO_VERIFY.

# Track Definitions

## 1. Module-SIS Chameleon Hash Track

- Purpose: support the quick-paper target around Module-SIS chameleon hash / commitment.
- Inclusion criteria: explicit SIS / Module-SIS / lattice trapdoor / lattice commitment / chameleon hash / lattice primitive anchor.
- Exclusion criteria: generic hash, generic commitment, generic ZK, generic blockchain, or generic privacy papers without lattice/PQC anchor.
- Required anchor: SIS, Module-SIS, lattice trapdoor, lattice commitment, lattice signature, or post-quantum lattice primitive.
- Useful paper types: construction papers, proof-technique papers, parameterization papers, reproducible implementation papers, related-work maps.
- Output format: table with paper, anchor, use for definition/proof/parameters/implementation, action, TODO_VERIFY.
- Action categories: read_now, skim, backlog, watch, exclude, TODO_VERIFY.

## 2. Xingye Lu Technical Bridge Track

- Purpose: track public technical literature bridging lattice primitives, ring signatures, linkable signatures, programmable hashes, and post-quantum privacy primitives.
- Inclusion criteria: technical paper with cryptographic primitive anchor and preferably lattice/PQC relation.
- Exclusion criteria: private PI material, generic ring signatures without PQC/lattice link, professor-specific application notes.
- Required anchor: lattice/PQC primitive, ring signature with post-quantum relevance, programmable hash with cryptographic relevance, or verified technical bridge.
- Useful paper types: linkable ring signatures, lattice signatures, hash-then-one-way signatures, lattice IBE, commitments.
- Output format: technical bridge table.
- Action categories: skim, backlog, watch, TODO_VERIFY, exclude.

## 3. MLWE / ML-KEM / ML-DSA Background Track

- Purpose: maintain standards and implementation maturity background.
- Inclusion criteria: explicit MLWE, ML-KEM, Kyber, ML-DSA, Dilithium, FIPS 203/204, rejection sampling, implementation audit, side-channel/fault/constant-time anchor.
- Exclusion criteria: generic PQC deployment without lattice scheme details.
- Required anchor: standardized lattice/PQC scheme or module-lattice background.
- Useful paper types: implementation audits, standard comparisons, parameter papers, side-channel/fault analyses.
- Output format: background table with escalation decision.
- Action categories: skim, watch, backlog, read_now when directly actionable.

## 4. AI4Lattice Longline Track

- Purpose: track long-term AI-assisted lattice cryptanalysis opportunities.
- Inclusion criteria: AI/ML explicitly connected to LWE/RLWE/MLWE/SIS/NTRU, BKZ, dual/primal/hybrid attack, cryptanalytic ranking, support recovery, or modular arithmetic in cryptographic context.
- Exclusion criteria: generic AI, generic LLM, generic optimization, generic federated learning, generic privacy ML.
- Required anchor: lattice attack or cryptographic hard-problem context.
- Useful paper types: coordinate selection, support recovery, learned pruning, attack-cost proxy, structured RLWE/MLWE modeling.
- Output format: watchlist with baseline, feature/label idea, hype risk, TODO_VERIFY.
- Action categories: watch, backlog, TODO_VERIFY, exclude.

## 5. Lattice/PQC Privacy and Registration-Based Encryption Watchlist

- Purpose: monitor privacy primitives only when lattice/PQC/HE/FHE anchored.
- Inclusion criteria: lattice ring signatures, lattice group signatures, FHE / RLWE secure aggregation, lattice-based anonymous credentials, lattice/PQC registration-based encryption.
- Exclusion criteria: generic privacy, generic registration, generic anonymous credentials, generic ZK without lattice/PQC anchor.
- Required anchor: lattice/PQC/HE/FHE assumption or construction.
- Useful paper types: privacy primitives, FHE systems, registration-based encryption with PQC anchor.
- Output format: watchlist table; escalation only after anchor verification.
- Action categories: watch, skim, backlog, exclude, TODO_VERIFY.

## 6. Noise / Exclusion Track

- Purpose: prevent generic keyword matches from polluting research planning.
- Inclusion criteria: papers that match generic terms but lack hard anchor.
- Exclusion criteria: none; this is the exclusion bucket.
- Required anchor: if no hard anchor, list reason for exclusion.
- Output format: title, matched generic keyword, missing anchor, action.
- Action categories: exclude, TODO_VERIFY if uncertain.

# Track-Based Scoring Rubric

Scores are 0 to 5 and are triage signals, not final judgments.

| Dimension | 0 | 3 | 5 |
| --- | --- | --- | --- |
| lattice/PQC anchor strength | no anchor | plausible but needs verification | explicit lattice/PQC/HE/FHE anchor |
| direct relevance to Module-SIS chameleon hash | none | indirect proof/primitive background | direct SIS/Module-SIS/chameleon hash support |
| relevance to Xingye Lu bridge | none | ring/privacy primitive but uncertain anchor | explicit lattice/PQC signature/privacy bridge |
| relevance to MLWE / ML-KEM / ML-DSA | none | general PQC | direct standardized lattice scheme |
| relevance to AI4Lattice | generic AI only | cryptography-adjacent ML | explicit lattice attack / LWE / BKZ link |
| short-term paper potential | none | related-work value | can support artifact in 2-4 weeks |
| long-term PhD value | none | background | strong longline track value |
| implementation / reproducibility potential | none | maybe reproducible | provides parameters/code/checklist |
| novelty risk | very high unknown | moderate | low or controllable |
| verification burden | impossible / too broad | moderate | low and source-backed |

Recommended action mapping:

- read_now: anchor 5 and short-term or implementation value 4-5.
- skim: anchor 4-5 but indirect short-term value.
- backlog: strong long-term value but not urgent.
- watch: plausible but incomplete anchor.
- exclude: anchor 0-1 or generic-only.
- TODO_VERIFY: evidence missing or ambiguous.

# Weekly Report Template v0.1

The reusable template is stored in:

`docs/research_tracks/weekly_report_template_v0.1.md`

# Example Weekly Entries

Examples are stored in:

`docs/research_tracks/weekly_report_examples_v0.1.md`

Examples use public project artifacts and are marked as examples / TODO_VERIFY where needed.

# Migration from Phase 11 Style

Phase 11B / 11C / 11D remain useful as optional manual deep-reading phases. They should not be the default weekly automation.

Migration rule:

- Weekly output should produce track-based synthesis.
- Deep reading should be triggered only when a paper is directly actionable.
- If the user wants deep reading, it can happen in ChatGPT web or a separate manual phase.
- The repository should not create private application material.

# Automation Module Adjustment

- Daily Public Digest Run = discovery only.
- Weekly Public Synthesis Run = track-based synthesis.
- Full Manual Quality Run = occasional full public refresh.
- No default PhD private material.
- No default single-paper deep reading.
- No scheduled automation.

# Future Phase Plan

- Phase 12C: Module-SIS Chameleon Hash Related Work Radar.
- Phase 12D: Xingye Lu Bridge Literature Map.
- Phase 12E: Quick-Paper Artifact Skeleton.
- Phase 12F: Weekly Track Report Implementation Plan.

# TODO_VERIFY

- whether weekly synthesis code already supports custom report sections;
- whether track scoring can be implemented without changing ranking thresholds;
- whether current data records contain enough fields for track classification;
- whether keyword policy requires code change or only template change;
- whether negative keyword policy should be enforced in code later;
- whether future implementation should add track labels to JSON records without changing relevance labels.

# Boundary Statement

This phase is documentation and template design only. No source ingestion, ranking thresholds, taxonomy semantics, section classifier, query expansion, negative keyword semantics, workflow semantics, release metadata, generated digest artifacts, `papers.db`, `.env`, secrets, or `PhD_Application` files are modified.
