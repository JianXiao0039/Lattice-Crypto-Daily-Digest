# Phase 12D Xingye Lu Bridge Literature Map

生成日期：2026-06-04

本报告属于公开 lattice/PQC research radar / literature-map 工作流。它不包含 target PI email、SoP draft、private application tracker、funding strategy、personal PhD narrative 或 private advisor-specific material。

# Executive Summary

This bridge map exists to connect the short-term **Module-SIS chameleon hash** quick-paper track with public technical directions that may be useful around linkable signatures, hash-then-one-way signatures, programmable hash functions, lattice privacy primitives, and commitment/chameleon-hash style constructions.

The purpose is technical, not private application planning. This document does not claim any verified fact about Xingye Lu. The phrase "Xingye Lu bridge" is used here only as a public technical bridge label inherited from earlier track documents, and all professor-specific facts remain `TODO_VERIFY`.

For the Module-SIS chameleon hash track, the most useful bridge is not a generic ring-signature queue. The useful bridge is a narrower map:

- commitments and chameleon hash as collision/adaptation primitives;
- SIS / Module-SIS as the assumption layer;
- programmable hash / hash-then-one-way signatures as proof-technique and primitive-design background;
- lattice-based linkable ring signatures and anonymous authentication as adjacent privacy/signature contexts;
- MLWE / ML-KEM / ML-DSA as background only unless they help parameterization or reproducibility;
- AI4Lattice as longline only, not a short-term construction dependency.

Current evidence from Phase 12C says no W23 item is verified as a direct Module-SIS chameleon hash construction. The strongest immediate action is therefore to build a `TODO_VERIFY` literature queue, verify exact papers in ChatGPT web or original sources, and transfer only public technical findings to the Module-SIS artifact workspace.

# Input Evidence Used

| Input | Status | How used | Limitation |
| --- | --- | --- | --- |
| `docs/reports/phase-12a-module-sis-chameleon-hash-track-calibration.md` | available | Strategy shift and track boundaries | Strategy only; no code behavior changed |
| `docs/reports/phase-12b-track-based-weekly-report-template.md` | available | Track-based weekly design and action categories | Template only |
| `docs/reports/phase-12c-module-sis-chameleon-hash-related-work-radar.md` | available | Recent candidate list and gap analysis | Metadata-level triage; original papers mostly unread |
| `docs/research_tracks/xingye_lu_bridge_track.md` | available | Public technical bridge policy | Explicitly excludes private PI material |
| `docs/research_tracks/module_sis_chameleon_hash_track.md` | available | Primary quick-paper inclusion/exclusion rules | Requires original-paper verification |
| `docs/research_tracks/module_sis_chameleon_hash_related_work_radar_v0.1.md` | available | Related-work categories and candidate queue | Not a proof or final related-work section |
| `docs/research_tracks/module_sis_chameleon_hash_todo_verify_queue_v0.1.md` | available | Existing verification gaps | Queue only |
| `data/weekly/2026-W23.json` | available from Phase 12C extraction | Candidate titles, IDs, labels, tags | Generated metadata; not original paper content |
| `D:\ResearchArtifacts\module-sis-chameleon-hash\research_radar\phase-12c-related-work-handoff.md` | available | Existing handoff queue | Read-only input |
| `D:\ResearchArtifacts\module-sis-chameleon-hash\research_radar\todo_verify_literature_queue.md` | available | Artifact-side TODO groups | Read-only input |

# Bridge Map Overview

| Bridge direction | Relevant primitive / concept | Possible relation to Module-SIS chameleon hash | Possible relation to Xingye Lu direction | Evidence source | Verification status | TODO_VERIFY | Recommended action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Linkable ring signatures | linkable signatures, anonymous authentication, lattice signatures | May provide adjacent privacy/signature related work and comparison context, not a direct construction input unless commitment/chameleon-hash mechanism appears | Possible technical bridge only; no professor fact claimed | `xingye_lu_bridge_track.md`, Phase 12C queue | Unverified | Verify lattice/PQC anchor and assumptions before using | skim |
| Hash-then-one-way signatures | hash-then-one-way paradigm, one-way functions, signature proof pattern | May inform how hash-like primitives are embedded into signature constructions | Possible technical bridge label only | User-provided Phase 12D direction | Unverified | Find concrete papers and verify lattice/PQC relation | backlog |
| Programmable hash functions | programmable hash, proof programming, trapdoor programming | Could help frame trapdoor collision/adaptation intuition if lattice/PQC anchored | Possible bridge to primitive-design literature | Phase 12A/12C keyword policy | Unverified | Reject generic programmable hash without lattice/PQC anchor | watch |
| Lattice-based privacy primitives | ring signatures, group signatures, anonymous credentials, privacy-preserving authentication | May motivate why chameleon hash / commitment-like primitives matter in privacy systems | Possible bridge to anonymous-authentication literature | `xingye_lu_bridge_track.md` | Unverified | Verify exact assumption and construction | skim |
| Commitments and chameleon hash | lattice commitment, SIS commitment, trapdoor collision, equivocation/adaptation | Directly relevant to definition, security model, and related work | Technical bridge through commitment/chameleon-hash primitives | Phase 12C radar and TODO queue | Partially mapped, not paper-verified | Find classical and lattice chameleon hash references | read_now |
| SIS / Module-SIS primitive construction | SIS, Module-SIS, norm bounds, trapdoors, gadget matrix | Core assumption and construction layer for quick-paper target | Technical bridge through lattice primitive design | Module-SIS track docs | Track-level verified; specific papers unverified | Verify parameters, assumption variants, proof obligations | read_now |
| MLWE / ML-KEM / ML-DSA background only | Module-LWE, ML-KEM, ML-DSA, rejection sampling, implementation audit | Useful maturity, parameter, and reproducibility background; not direct chameleon hash core | Background only unless technical bridge is explicit | Phase 12C candidate table | Metadata-level | Do not let standards papers dominate quick-paper related work | backlog |
| AI4Lattice longline | LWE/RLWE/MLWE attacks, BKZ, hybrid attacks, coordinate selection | Not needed for first Module-SIS chameleon hash construction; possible long-term parameter/security tooling | Longline only, not professor-specific | Phase 12A strategy | Out of short-term scope | Keep separate from primitive construction unless concrete artifact emerges | watch |

# What Can Support the Small Paper

## Related Work for Introduction

Use this section to motivate why a post-quantum chameleon hash / commitment-adjacent primitive is worth studying.

Candidate inputs:

- classical chameleon hash definitions: `TODO_VERIFY`;
- lattice-based chameleon hash papers: `TODO_VERIFY`;
- lattice commitments and SIS / Module-SIS commitments: `TODO_VERIFY`;
- lattice-based linkable signatures and anonymous authentication as adjacent motivation, only after lattice/PQC anchor is verified.

Do not cite a generic ring signature paper as support for the small paper unless it is cryptographically and lattice/PQC anchored.

## Related Work for Construction Motivation

Useful bridge concepts:

- SIS / Module-SIS collision resistance;
- lattice trapdoors and preimage sampling;
- commitment binding / hiding / equivocation vocabulary;
- chameleon hash trapdoor collision / adaptation interface;
- programmable hash only when a lattice/PQC proof technique is verified.

Phase 12C found no direct W23 construction paper, so this section should start from targeted literature search rather than recent digest-only candidates.

## Related Work for Security Model

Potentially relevant model components:

- collision resistance against users without trapdoor;
- trapdoor-enabled collision finding / adaptation;
- key generation and trapdoor ownership;
- public parameter generation;
- norm-bound and module-rank constraints;
- honest limitation: proof sketch first, full reduction only after verification.

`TODO_VERIFY`: identify which classical chameleon hash security notions transfer cleanly to a Module-SIS setting.

## Related Work for Comparison Table

Comparison dimensions to prepare:

- assumption: RSA/discrete-log/SIS/Module-SIS/LWE/other;
- trapdoor type;
- collision/adaptation interface;
- hash/opening size;
- parameter transparency;
- implementation availability;
- proof status;
- post-quantum claim scope.

Do not fill performance numbers until implementation or source papers provide them.

## Related Work for Future Work / Advisor Discussion

Public technical topics suitable for future work:

- linkable ring signatures and anonymous authentication as adjacent applications;
- hash-then-one-way signature patterns if a concrete lattice paper is verified;
- programmable hash / IBE-adjacent primitive design if anchored;
- MLWE / ML-KEM / ML-DSA standards background for parameterization discipline;
- AI4Lattice tooling only as long-term support for security/parameter triage.

# Xingye Lu Bridge Caution Policy

This project must not invent professor facts.

Do not claim:

- current affiliation unless verified;
- current recruitment or funding unless verified;
- paper authorship unless verified from official/public sources;
- research fit as fact;
- that any private application strategy exists in this public repo.

Safe wording:

- "possible technical bridge";
- "needs verification";
- "public technical literature map";
- "ring-signature / anonymous-authentication technical direction";
- "lattice/PQC primitive bridge".

Unsafe wording:

- "this is a confirmed advisor fit";
- "this professor works on X" without source;
- "email angle" or "application strategy" in this public repo;
- private target PI notes or SoP material.

# Candidate Reading Queue

## read_now

| Title / topic | Reason | Bridge direction | How it may support Module-SIS chameleon hash | TODO_VERIFY |
| --- | --- | --- | --- | --- |
| Classical chameleon hash definitions | Directly needed for interface and security model | commitments and chameleon hash | Defines keygen/hash/adapt/verify and collision/adaptation language | Find authoritative source and extract definitions |
| Lattice-based chameleon hash papers | Directly relevant if found | commitments and chameleon hash | Baseline for novelty, assumptions, comparison table | Search and verify exact constructions |
| SIS / Module-SIS commitment papers | Core assumption layer | SIS / Module-SIS construction | Helps map binding/collision resistance and norm bounds | Verify assumption variants and parameters |
| Lattice trapdoor / preimage sampling references | Needed for trapdoor collision intuition | programmable/trapdoor primitive design | May support adaptation mechanism or limitations | Verify whether compatible with Module-SIS goal |

## skim

| Title / topic | Reason | Bridge direction | How it may support Module-SIS chameleon hash | TODO_VERIFY |
| --- | --- | --- | --- | --- |
| BRaccoon: Concurrently Secure Blind Lattice Signatures from Raccoon | Lattice signature/privacy primitive context from Phase 12C | linkable / anonymous authentication adjacency | May inform related-work framing around lattice privacy/signature primitives | Verify assumptions and whether commitment/chameleon concepts appear |
| Witness Pseudorandom Functions for Vector Commitments and Applications | Commitment-related item from Phase 12C | commitments | May clarify vector commitment vocabulary | Verify whether it is lattice-based and relevant |
| Improved Dual Attack and Trapdoor Sampling via Quantum Rejection Sampling | Trapdoor sampling appears in title | trapdoor / sampling background | May inform trapdoor limitations or terminology | Verify original scope before using |
| Identity-Based Revocable and Linkable Ring Signature | Linkable ring signature title from Phase 12C | linkable ring signature bridge | Possible bridge only if lattice/PQC anchored | Verify anchor; exclude if generic/non-lattice |

## backlog

| Title / topic | Reason | Bridge direction | How it may support Module-SIS chameleon hash | TODO_VERIFY |
| --- | --- | --- | --- | --- |
| Hash-then-one-way signatures | User-provided technical bridge direction | hash-then-one-way | Possible proof/design vocabulary | Find concrete papers and lattice/PQC anchor |
| Programmable hash functions with lattice anchor | Possible proof-programming background | programmable hash | Could help with trapdoor/adaptation framing | Reject generic programmable hash |
| Lattice-based privacy primitives | Adjacent application motivation | privacy primitives | May motivate future application section | Verify exact assumption and primitive |
| ML-KEM / ML-DSA implementation audit papers | Standards maturity background | MLWE / PQC background | May improve reproducibility discipline | Do not use as direct chameleon hash support |

## watch

| Title / topic | Reason | Bridge direction | How it may support Module-SIS chameleon hash | TODO_VERIFY |
| --- | --- | --- | --- | --- |
| AI4Lattice coordinate selection / hybrid attack papers | Long-term track, not immediate construction | AI4Lattice | Could later support parameter/security triage | Keep separate from quick-paper proof |
| FHE / RLWE systems papers | Background only | PQC privacy / HE | May help broader PQC maturity | Escalate only if cryptographic primitive lesson transfers |
| Generic anonymous-authentication papers | Potential but noisy | privacy primitives | Watch only if lattice/PQC anchor is explicit | Exclude without anchor |

## exclude

| Title / topic | Reason | Bridge direction | How it may support Module-SIS chameleon hash | TODO_VERIFY |
| --- | --- | --- | --- | --- |
| Generic hash papers | Missing lattice/SIS/PQC anchor | none | no support | Exclude unless anchor appears |
| Generic commitment papers | Missing lattice/SIS/PQC anchor | none | no support | Exclude unless anchor appears |
| Generic ring signature papers | Missing PQC/lattice relation | none | no support | Verify before watchlist |
| Generic privacy / registration / blockchain / AI papers | Keyword-only match risk | none | no support | Exclude unless explicit lattice/PQC/HE/FHE anchor |

# Small Paper Integration Matrix

| Paper section | Required related work | Xingye bridge relevance | Module-SIS relevance | Risk | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- |
| Introduction | classical chameleon hash, post-quantum motivation, lattice commitments | bridge as motivation only | high | overclaiming application fit | Verify exact prior chameleon hash and lattice commitment papers |
| Related Work | lattice chameleon hash, SIS commitments, lattice signatures, linkable signatures | medium if lattice/PQC linkable signatures are verified | high | citation drift | Read original papers before naming them |
| Preliminaries | SIS / Module-SIS, norms, module lattices, trapdoors | low | core | mixing SIS and LWE incorrectly | Verify assumptions and notation |
| Construction | hash/adapt/verify interface, trapdoor collision | low | core | unverified trapdoor mechanism | Do not claim construction until formal draft exists |
| Security Model | collision resistance, trapdoor adaptation, parameter constraints | medium through signature/privacy analogies | core | proof overclaim | Mark proof sketch vs full reduction |
| Parameterization | norm bounds, modulus, dimension/rank, estimator input | low | core | unsafe parameter claims | Use reproducible scripts later |
| Implementation | Python/Sage toy artifact, tests, reproducibility manifest | low | medium | confusing toy with production | State non-production scope |
| Limitations / Future Work | linkable signatures, privacy primitives, AI4Lattice tooling | high as future technical bridge | medium | drifting into private PI material | Keep public and technical |

# Handoff to ResearchArtifacts

Target workspace:

`D:\ResearchArtifacts\module-sis-chameleon-hash`

Created handoff file:

`research_radar/phase-12d-xingye-lu-bridge-handoff.md`

Handoff plan:

- bridge papers to verify:
  - classical chameleon hash;
  - lattice-based chameleon hash;
  - SIS / Module-SIS commitments;
  - lattice trapdoor / preimage sampling;
  - lattice-based linkable ring signatures;
  - hash-then-one-way / programmable hash with lattice/PQC anchor.
- concepts to include in related work:
  - commitment vs chameleon hash;
  - trapdoor collision / adaptation;
  - lattice signature / anonymous authentication only as adjacent context;
  - reproducible parameterization.
- concepts to avoid overclaiming:
  - professor-specific fit;
  - unverified authorship;
  - performance claims;
  - full security proof;
  - production-ready implementation.
- possible comparison dimensions:
  - assumption;
  - trapdoor type;
  - collision/adaptation interface;
  - parameter transparency;
  - implementation availability;
  - limitation.

# Next Actions

Topics to read in ChatGPT web:

1. classical chameleon hash definitions and security notions;
2. lattice-based chameleon hash papers;
3. SIS / Module-SIS commitment papers;
4. lattice trapdoor / GPV-style preimage sampling background;
5. lattice-based linkable ring signature papers only after lattice/PQC anchor is verified.

Topics to add to small-paper related work after verification:

- commitment vs chameleon hash distinction;
- SIS / Module-SIS assumption mapping;
- trapdoor collision mechanism;
- lattice signature / anonymous-authentication adjacent use cases;
- parameterization and reproducibility methodology.

Topics that should wait for official verification:

- any Xingye Lu-specific professor fact;
- any current affiliation / recruitment statement;
- any concrete claim about hash-then-one-way signature relation;
- any performance or security comparison.

Items that should feed into Phase RA-1:

- a related-work matrix;
- a TODO_VERIFY queue;
- a construction feasibility matrix;
- a preliminary interface: keygen / hash / adapt / verify;
- a parameter placeholder table.

# TODO_VERIFY

- Verify direct lattice-based chameleon hash literature.
- Verify SIS / Module-SIS commitment references.
- Verify whether `BRaccoon` has assumptions or proof patterns useful for the quick-paper track.
- Verify whether `Witness Pseudorandom Functions for Vector Commitments and Applications` is lattice-based and commitment-relevant.
- Verify whether `Identity-Based Revocable and Linkable Ring Signature` is lattice/PQC anchored before using it.
- Verify concrete hash-then-one-way signature papers and whether they are lattice/PQC related.
- Verify programmable hash papers and reject generic non-lattice versions.
- Verify any Xingye Lu-specific fact from official/public sources before writing it anywhere.
- Verify that future weekly reports can produce bridge sections without changing ranking thresholds.
