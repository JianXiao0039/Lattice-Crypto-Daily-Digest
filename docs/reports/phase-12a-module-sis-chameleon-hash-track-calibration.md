# Phase 12A Module-SIS Chameleon Hash Track Calibration

生成日期：2026-06-04

本报告属于公开 lattice/PQC research tooling track。它不包含 SoP draft、target PI email、private application tracker、personal PhD narrative、funding strategy 或 private advisor-specific material。

# Executive Summary

本阶段调整项目策略：单篇论文深读通常由 ChatGPT web 完成，本仓库不再默认承担 single-paper deep reading 生产线。公开仓库应回到更适合自动化和可复用的角色：research radar、topic clustering、relevance judgment、idea backlog 和 public reproducibility support。

新的短期核心是：

**A Module-SIS-Based Post-Quantum Chameleon Hash Primitive with Reproducible Parameterization and Implementation**

长期保留三条辅助线：

- Xingye Lu-related technical bridge, only as technical literature bridge, not private PI material;
- MLWE / ML-KEM / ML-DSA background assets;
- AI4Lattice long-term PhD track support, framed as public technical watchlist.

Hard anchoring rule:

Generic keywords are not enough. A paper containing "hash", "commitment", "ring signature", "privacy", "AI", "LLM", "registration", "blockchain", or "ZK" should not be included unless it has a clear lattice/PQC/HE/FHE/LWE/RLWE/MLWE/SIS/Module-SIS/NTRU/ML-KEM/ML-DSA anchor.

# Current Problem

The current workflow can over-focus on high-score single papers. High relevance score is useful, but it does not always mean immediate usefulness for the user's current quick-paper target.

Observed mismatch:

- A paper such as `On the Secrecy of the Encapsulation Coin in ML-KEM` is valuable for PQC implementation maturity, but it is not the current quick-paper core.
- Deep reading packs are useful occasionally, but they are less valuable as a default repository output.
- The short-term research need is not "read every A-level paper deeply"; it is "find papers that support Module-SIS chameleon hash construction, parameterization, proof framing, implementation, and related-work positioning".
- Generic privacy / AI / commitment / hash papers can pollute the queue if not lattice/PQC anchored.

# New Project Role

This repository should act as:

- lattice/PQC paper radar;
- topic clustering engine;
- Module-SIS chameleon hash support tool;
- Xingye Lu technical bridge monitor;
- AI4Lattice long-term watchlist;
- reproducible implementation / parameterization support;
- source health and coverage audit tool;
- public research workflow notebook, not private application workspace.

# Research Track Map

| Track | Purpose | Short-term value | Long-term value | Key assumptions / primitives | Inclusion criteria | Exclusion criteria | Weekly output expectation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Module-SIS Chameleon Hash | Support quick-paper target around Module-SIS chameleon hash / commitment | directly feeds definition, proof sketch, parameterization, related work | lightweight lattice primitive line | SIS, Module-SIS, trapdoors, commitments, chameleon hash, lattice signatures | explicit SIS/Module-SIS/lattice commitment/chameleon hash/trapdoor anchor | generic hash/commitment without lattice/PQC anchor | 3-5 papers or notes directly useful for construction/proof/parameters |
| Xingye Lu Technical Bridge | Track technical literature bridges to linkable signatures and privacy primitives | helps map ring signature / programmable hash / commitment literature | public technical bridge to post-quantum privacy primitives | lattice signatures, linkable ring signatures, hash-then-one-way signatures, programmable hash, IBE | verified technical anchor; no professor claims | private PI matching; generic signature without PQC/lattice relevance | bridge candidates and TODO_VERIFY paper list |
| MLWE / ML-KEM / ML-DSA Background | Maintain PQC maturity and standards awareness | supports parameter/security background | standard-facing PQC track | MLWE, ML-KEM, ML-DSA, Kyber, Dilithium, rejection sampling | standards, implementation, parameter, security review papers | generic PQC deployment without lattice schemes | background summary and escalation candidates |
| AI4Lattice Longline | Track long-term AI-assisted lattice cryptanalysis opportunities | gives future experiment seeds | PhD-longline technical watchlist | LWE/RLWE/MLWE, sparse LWE, BKZ, dual/primal/hybrid, coordinate selection | AI/ML explicitly tied to lattice attacks or cryptanalysis | generic AI/LLM/optimization | watchlist with baseline / dataset / feature ideas |
| Lattice/PQC Privacy and Registration-Based Encryption Watchlist | Monitor privacy primitives only when lattice/PQC anchored | related-work background for primitive track | privacy primitive research option | lattice ring signatures, anonymous credentials, FHE, RBE if PQC anchored | explicit lattice/PQC/HE/FHE assumption or construction | generic privacy, FL, DP-SGD, ZK, registration | watchlist only; escalate only after anchor verified |

# Module-SIS Chameleon Hash Track

## Target paper idea

A Module-SIS-Based Post-Quantum Chameleon Hash Primitive with Reproducible Parameterization and Implementation.

## What papers to capture

- Module-SIS / SIS commitments.
- Lattice trapdoor functions.
- Chameleon hash from lattices.
- SIS-based collision or adaptation mechanisms.
- Lattice-based commitments and programmable hashes.
- Lattice signatures and linkable signatures with reusable proof ideas.
- Parameter estimation and implementation papers that help choose matrix dimensions, modulus, norm bounds, sampling method, and security margin.

## Useful keywords

- Module-SIS
- SIS
- lattice commitment
- chameleon hash
- trapdoor collision
- trapdoor function
- lattice trapdoor
- programmable hash
- lattice signature
- linkable ring signature
- rejection sampling
- gadget matrix
- discrete Gaussian
- parameter estimation

## Required lattice/PQC anchors

At least one of:

- SIS / Module-SIS / MSIS
- lattice trapdoor / GPV / gadget matrix
- lattice commitment / SIS commitment
- lattice-based signature / ring signature
- post-quantum primitive with lattice assumption

## What to exclude

- generic hash papers;
- generic commitment papers;
- generic blockchain hash usage;
- generic ZK without lattice/PQC anchor;
- generic privacy or credential systems without lattice/PQC anchor;
- papers where "lattice" means physics/materials/combinatorics.

## Weekly output format

- Direct construction support: 1-3 papers.
- Proof / assumption support: 1-3 papers.
- Parameter / implementation support: 1-3 papers.
- Related-work only: short list.
- TODO_VERIFY: explicit assumption and construction checks.

## TODO_VERIFY policy

Do not claim a paper supports Module-SIS chameleon hash until the assumption, trapdoor mechanism, and security goal are verified from the original paper.

# Xingye Lu Bridge Track

This is a public technical bridge, not a private PI strategy.

## Topics to watch

- linkable ring signatures;
- hash-then-one-way signatures;
- programmable hash;
- lattice primitive bridge;
- post-quantum privacy primitives;
- IBE-adjacent lattice primitives;
- lattice-based anonymous authentication.

## Avoiding professor-specific claims

Do not write:

- professor fit claims;
- target PI emails;
- application strategy;
- recruitment/funding notes;
- personal positioning.

Allowed public wording:

- "technical bridge to linkable ring signatures";
- "ring-signature / anonymous-authentication literature";
- "lattice/PQC privacy primitive watchlist".

## TODO_VERIFY policy

Only classify a paper into this track after verifying the paper's technical content. A ring signature paper is not automatically lattice/PQC.

# AI4Lattice Longline Track

## Watch topics

- Swin-guided coordinate selection;
- sparse LWE / RLWE / MLWE;
- dual / primal / hybrid attacks;
- BKZ / lattice reduction interface;
- support recovery;
- learned pruning;
- attack-cost proxy;
- parameter prediction;
- structured RLWE / MLWE representation;
- negative-cyclic modeling.

## Exclusion policy

Exclude generic AI unless it explicitly connects to:

- LWE/RLWE/MLWE/SIS/NTRU;
- lattice cryptanalysis;
- BKZ / dual / primal / hybrid attacks;
- modular arithmetic in cryptographic setting;
- cryptanalytic search or ranking.

## Weekly output format

- candidate paper;
- classical baseline it may connect to;
- possible feature / label / dataset;
- risk of hype;
- TODO_VERIFY.

# ML-KEM / ML-DSA Background Track

## What to keep watching

- ML-KEM randomness / coin security;
- ML-KEM / Kyber implementation issues;
- ML-DSA / Dilithium rejection sampling and reduction placement;
- side-channel / fault / constant-time issues;
- FIPS 203 / 204 context;
- reproducible PQC implementation artifacts.

## When to escalate to reading

Escalate if:

- it affects ML-KEM / ML-DSA security assumptions or implementation correctness;
- it provides reproducible parameters or test cases;
- it gives a checklist useful for implementation maturity;
- it informs Module-SIS / MLWE background.

## When not to generate artifact

Do not generate a full artifact if:

- the paper is useful but peripheral;
- it is a one-off implementation note;
- original paper was not read;
- the security claim is too strong and unverified;
- it does not support the short-term Module-SIS track.

# New Weekly Report Design

Future weekly reports should contain:

1. Directly useful for Module-SIS chameleon hash.
2. Useful for Xingye Lu bridge.
3. Useful background for MLWE / ML-KEM / ML-DSA.
4. AI4Lattice longline watchlist.
5. Excluded generic/noise papers.
6. TODO_VERIFY items.
7. Next 3 paper-reading candidates for ChatGPT web.

The "Next 3 paper-reading candidates" section should be the handoff point to ChatGPT web, not a trigger for this repository to produce automatic deep reading packs.

# Automation Module Adjustment

- Daily = discovery only.
- Weekly = track-based synthesis.
- Full = occasional public research refresh.
- No default single-paper deep reading.
- No PhD private material.
- No scheduled automation.
- No background task.

# Future Phase Plan

Replace Phase 11E/11F with:

- Phase 12B: Track-Based Weekly Report Template.
- Phase 12C: Module-SIS Chameleon Hash Related Work Radar.
- Phase 12D: Xingye Lu Bridge Literature Map.
- Phase 12E: Quick-Paper Artifact Skeleton.

# TODO_VERIFY

Before implementation:

- verify existing taxonomy file locations;
- verify current scoring signals;
- verify current query expansion behavior;
- verify current negative keyword behavior;
- decide whether new tracks require code changes or only report-template changes;
- decide whether `research_artifacts/` should remain ignored or selectively public;
- decide how to separate public technical bridge docs from private application material.

# Boundary Statement

This is documentation and strategy calibration only. No source ingestion, ranking thresholds, taxonomy semantics, section classifier, query expansion, negative keyword semantics, workflow semantics, release metadata, generated digest artifacts, `papers.db`, `.env`, secrets, or `PhD_Application` files are modified.
