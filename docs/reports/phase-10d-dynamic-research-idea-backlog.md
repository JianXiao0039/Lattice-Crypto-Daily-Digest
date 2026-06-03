# Phase 10D Dynamic Lattice/PQC Research Idea Backlog

生成日期：2026-06-04

本报告基于近期 digest、Phase 10A-C 报告和 Top 3 paper note scaffolds，生成一个动态研究 idea backlog。它不是论文结论，也不是已验证 novelty claim。所有技术细节在原文精读、代码复现、参数核验或导师讨论前均保持 TODO_VERIFY。

# Executive Summary

当前最值得推进的短期方向不是单一路线，而是三条互补研究线：

1. **AI4Lattice / LWE attack-assistance**：以 `Unified Dual Attack Analyses`、`From Perfect to Approximate Hints`、`CoNAN` 为证据，发展 learning-assisted attack cost proxy、coordinate ranking、support recovery 或 structured lattice cryptanalysis benchmark。
2. **PQC implementation security**：以 `On the Secrecy of the Encapsulation Coin in ML-KEM` 和 `When Removing Reductions Goes Wrong` 为证据，发展 ML-KEM / ML-DSA implementation audit checklist 或 reproducible review artifact。
3. **Module-SIS / lattice primitive line**：以用户长期主线和 `BRaccoon`、lattice signatures / commitments / privacy primitives 为背景，保持 Module-SIS chameleon hash / commitment 的短期 artifact 方向，但不要把 MLWE attack claim 直接迁移到 SIS。

建议当前主线：

- Primary short-term track：ML-KEM randomness / encapsulation coin security review and reproducible check。
- Secondary track：dual-attack score distribution based AI4Lattice benchmark。
- Long-term PhD track：classical-grounded AI-assisted lattice cryptanalysis plus deployable PQC implementation security。

# Input Evidence Used

| Input | Status | How used |
| --- | --- | --- |
| `docs/reports/phase-10c-advisor-weekly-update.md` | available | 提取导师汇报问题、Top 3 论文、风险与下周计划 |
| `docs/reports/phase-10b-top-3-obsidian-notes.md` | available | 提取 Top 3 selected papers、recommended reading order、best use by purpose |
| `notes/papers/*.md` | available | 提取三张 paper note scaffold 中的 paper facts、背景补充、我的推断 |
| `docs/reports/phase-10a-research-reading-pipeline.md` | available | 提取 must-read / secondary-watch / noise / source health caveats |
| `data/weekly/2026-W23.json` | available | 提取 W23 coverage、ranking、sections、A/B/C label distribution |
| `data/2026-06-03.json` | available | 提取 6 月 3 日 ML-KEM 论文、source health 和 daily priority |
| `digests/weekly/2026-W23.md` | available | 作为 weekly narrative 的背景，不直接复制结论 |
| `digests/2026-06-03.md` | available | 作为 daily narrative 的背景，不直接复制结论 |
| `state/reading-queue.json` | available | 只读检查 TODO_READ / TODO_VERIFY 状态 |
| `exports/research-progress/2026-W23/` | available | 只读参考 advisor draft 和 verification backlog |

# Dynamic Focus Map

| Focus area | Evidence strength | Recent paper support | User fit | Short-term paper potential | Long-term PhD narrative potential | Risk level | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Module-SIS / SIS primitives | Medium | BRaccoon; Witness PRF / vector commitments; user Module-SIS chameleon hash artifact | Very high | Medium | High | Medium | Keep as secondary construction track; avoid overclaiming from MLWE papers |
| MLWE / RLWE / LWE | Very high | Unified Dual Attack; Module Lattice Security Part IV; From Perfect to Approximate Hints | Very high | High | Very high | Medium-high | Primary theory / attack reading track |
| ML-KEM / Kyber | Very high | ML-KEM coin paper; Unified Dual Attack; Module Lattice Security | Very high | High | Very high | Medium | Use for implementation security plus security-estimation narrative |
| ML-DSA / Dilithium | Medium-high | Removing Reductions in ML-DSA; Unified Dual Attack mentions Dilithium context | High | Medium | High | Medium | Use as implementation-security secondary benchmark |
| lattice reduction / attacks | Very high | Unified Dual Attack; Improved Dual Attack; CoNAN; From Perfect to Approximate Hints | Very high | High | Very high | Medium | Build attack-assistance backlog around score/ranking/support recovery |
| AI-assisted lattice cryptanalysis | High | Unified Dual Attack; CoNAN; sparse LWE hints; user Swin-guided coordinate selection | Very high | Medium-high | Very high | Medium-high | Pursue classical-grounded AI4Lattice, not end-to-end breaking |
| lattice/PQC privacy primitives | Medium | BRaccoon; lattice signatures; possible commitments / credentials | High | Medium | High | Medium | Keep as related-work and primitive map track |
| implementation / side-channel / reproducibility | Very high | ML-KEM coin; ML-DSA reductions; GPU LWE KEMs | High | Very high | High | Medium | Best short-term concrete artifact path |
| FHE / RLWE secure aggregation | Medium | CKKS / BGV / TFHE papers; GBDT privacy paper watchlist | Medium | Medium | Medium | Medium-high | Include only when FHE/RLWE parameters or implementation are explicit |
| source health / literature triage reproducibility | Medium | IACR latest/RSS recovery; source coverage audit; optional Semantic Scholar enrichment | High | Medium | Medium | Low-medium | Useful tooling note, not core crypto paper unless framed carefully |

# Idea Backlog

## IDEA-10D-01

## Working title

ML-KEM Encapsulation Coin Security Review and Reproducible Audit Checklist

## Category

implementation

## Core question

Can I turn the ML-KEM encapsulation coin secrecy paper into a conservative, reproducible audit checklist that distinguishes paper facts, library behavior, configuration assumptions, and TODO_VERIFY items?

## Lattice/PQC anchor evidence

The recent digest includes `On the Secrecy of the Encapsulation Coin in ML-KEM`, IACR ePrint 2026/1117, A / 100, ML-KEM / Kyber anchored.

## 论文事实

- Digest metadata says the paper studies ML-KEM encapsulation coin secrecy.
- Digest abstract mentions ML-KEM, FIPS 203, and several libraries.
- Phase 10B generated an Obsidian scaffold for this paper.

## 背景补充

ML-KEM / Kyber implementation security depends not only on mathematical assumptions, but also on randomness handling, API exposure, build configuration, and validated deployment settings.

## 我的推断

This can become a near-term implementation-security artifact without claiming new cryptanalysis: a structured checklist plus, if feasible later, small reproducibility scripts.

## Minimum viable version

Within 2-4 weeks: read the paper, build a table of libraries / behavior / attacker capability / configuration / TODO_VERIFY, and write a short audit checklist.

## Stronger version

Workshop-quality note: add minimal reproduction attempts for safe test cases, compare with ML-KEM implementation guidelines, and propose a checklist for PQC library maintainers.

## Required knowledge

ML-KEM basics, Kyber encapsulation, randomness handling, KEM API design, basic C / Go / library audit literacy, FIPS configuration awareness.

## Required artifacts

Paper note, library behavior table, audit checklist, optional reproduction scripts, experiment logs if any are actually run.

## Feasibility

5

## Novelty risk

3

## Implementation risk

3

## Advisor pitch

This is a safe short-term artifact: I am not claiming a break of ML-KEM, only organizing implementation-security evidence and verification steps from a new IACR paper. It connects deployable PQC and systems security.

## Why this helps 27fall PhD application

It shows I can bridge standardized lattice cryptography, implementation security, and reproducible research practice.

## Next 3 actions

1. Read the original paper's threat model and library table.
2. Create a TODO_VERIFY matrix for each library and configuration.
3. Ask advisor whether a reproduction checklist is worth pursuing.

## TODO_VERIFY

- Verify all library-specific claims.
- Verify whether behavior is production, test-only, build-time, or configuration-dependent.
- Verify whether any reproduction is safe and ethical.

## IDEA-10D-02

## Working title

Dual-Attack Score Distribution as an AI4Lattice Attack-Cost Proxy

## Category

attack-assistance

## Core question

Can score distribution and covariance features from dual attacks be used as classical-grounded labels for AI-assisted lattice attack ranking?

## Lattice/PQC anchor evidence

`Unified Dual Attack Analyses` is A / 100 with reading_priority_score 95 and is explicitly LWE / ML-KEM / dual attack anchored.

## 论文事实

- Digest metadata says the paper studies covariance-based score distribution prediction for LWE dual attacks.
- Phase 10B identifies it as the strongest AI4Lattice-relevant paper.

## 背景补充

Dual attack score distributions can influence success probability and false-positive behavior. AI4Lattice is safer when it assists classical attack pipeline components rather than claiming end-to-end key recovery.

## 我的推断

The paper may provide measurable targets for learning-to-rank, candidate filtering, or hard/easy instance separation.

## Minimum viable version

Within 2-4 weeks: summarize the score features and propose a small synthetic LWE benchmark design without running large experiments.

## Stronger version

Implement a toy LWE dataset, compute classical dual-attack score features, compare simple ranking heuristics with MLP / Transformer / Swin-style local feature models.

## Required knowledge

LWE dual attacks, score distributions, covariance, basic lattice estimator concepts, supervised learning, experimental design.

## Required artifacts

Paper note, feature list, toy LWE generator, baseline ranking scripts, result logs, ablation table.

## Feasibility

4

## Novelty risk

3

## Implementation risk

4

## Advisor pitch

This idea keeps AI4Lattice grounded: AI predicts or ranks classical attack signals rather than pretending to break real LWE. It can become a small benchmark or workshop-style artifact.

## Why this helps 27fall PhD application

It demonstrates a mature AI + cryptanalysis narrative with classical baselines and falsifiable experiments.

## Next 3 actions

1. Read the score distribution derivation.
2. Extract candidate features and labels.
3. Draft a toy benchmark protocol.

## TODO_VERIFY

- Verify which features are actually in the paper.
- Verify whether labels can be computed for toy instances.
- Verify novelty against existing ML attacks on LWE.

## IDEA-10D-03

## Working title

Module-LWE Quantum Attack Claim Verification Map

## Category

survey-plus-reproducibility

## Core question

How should I systematically verify the high-impact claim in `Module Lattice Security (Part IV)` before citing or building on it?

## Lattice/PQC anchor evidence

The paper is arXiv:2605.17412, A / 100, reading_priority_score 92, with MLWE / ML-KEM / Falcon / NTRU anchors.

## 论文事实

- Digest metadata reports a probabilistic polynomial quantum attack claim over 2-power cyclotomics.
- Phase 10B marks it as must-read but claim-sensitive.

## 背景补充

Strong lattice-security claims need assumption mapping, parameter scope, model clarity, and community cross-checking.

## 我的推断

This can become a verification note rather than a new attack paper: a careful map of definitions, assumptions, and open questions for advisor discussion.

## Minimum viable version

Within 2-4 weeks: read Parts I-IV, make a claim table, identify assumptions and parameter scope.

## Stronger version

Write a structured survey-plus-verification note comparing the claim with standard ML-KEM / Falcon / NTRU security assumptions and public responses.

## Required knowledge

MLWE, cyclotomic rings, quantum algorithms at a high level, PIP, parameter estimation, ML-KEM security assumptions.

## Required artifacts

Claim matrix, assumption map, parameter table, bibliography, advisor questions.

## Feasibility

3

## Novelty risk

2

## Implementation risk

2

## Advisor pitch

This is a risk controlled way to handle a potentially important but unverified claim. I can present what is claimed, what must be checked, and how it relates to ML-KEM security.

## Why this helps 27fall PhD application

It shows careful cryptographic judgment and the ability to evaluate high-stakes claims without overclaiming.

## Next 3 actions

1. Find Parts I-III.
2. Extract theorem statements and assumptions.
3. Ask advisor which claim should be verified first.

## TODO_VERIFY

- Verify all claimed complexity bounds.
- Verify applicability to real parameters.
- Verify whether there are critiques or independent confirmations.

## IDEA-10D-04

## Working title

Swin-Guided Coordinate Selection for Sparse LWE with Approximate Hints

## Category

attack-assistance

## Core question

Can approximate hint models for sparse LWE be converted into a small coordinate-selection benchmark for Swin or window-attention models?

## Lattice/PQC anchor evidence

`From Perfect to Approximate Hints` is A / 100 with reading_priority_score 89 and is anchored to LWE secret recovery, sparse / low-Hamming-weight secrets, and attack settings.

## 论文事实

- Phase 10A selected this as secondary-watch.
- Digest metadata says it concerns LWE secret recovery with low Hamming weight and approximate hints.

## 背景补充

Sparse LWE support recovery and coordinate selection are natural places for AI-assisted ranking, especially when hints or side information exist.

## 我的推断

This is a strong candidate for my Swin-guided coordinate selection line, because local/window attention can be tested as a structured ranking heuristic.

## Minimum viable version

Within 2-4 weeks: build a toy sparse LWE / approximate-hint reading note and define a tiny coordinate-ranking dataset.

## Stronger version

Run baseline random / heuristic / MLP / CNN / Swin-style models and compare support recovery precision under toy parameters.

## Required knowledge

Sparse LWE, hint leakage, support recovery, basic ML ranking, evaluation metrics.

## Required artifacts

Toy data generator, coordinate labels, baseline scripts, model config, false-positive metrics.

## Feasibility

4

## Novelty risk

4

## Implementation risk

4

## Advisor pitch

This is a concrete AI4Lattice experiment, but it stays honest by using toy settings and classical baselines.

## Why this helps 27fall PhD application

It directly supports the user's AI4Lattice research narrative with a reproducible, bounded experiment.

## Next 3 actions

1. Read the hint model from the paper.
2. Define toy sparse LWE instances.
3. Choose baseline metrics: precision, recall, false positive rate, attack-cost proxy.

## TODO_VERIFY

- Verify the exact hint model.
- Verify whether similar ML coordinate-selection work already exists.
- Verify toy-to-real limitation language.

## IDEA-10D-05

## Working title

CoNAN-Inspired Structure-Aware Lattice Cryptanalysis Benchmark

## Category

benchmark

## Core question

Can recent structure-aware cryptanalysis ideas be turned into a small benchmark for structured RLWE / MLWE feature representation?

## Lattice/PQC anchor evidence

`CoNAN: A Structure-Aware Framework for Lattice Cryptanalysis` is A / 100, reading_priority_score 83, and appears in Phase 10A secondary-watch.

## 论文事实

- Digest metadata identifies CoNAN as structure-aware lattice cryptanalysis.
- It is connected to LWE / MLWE, lattice reduction / attacks, and PQC implementation sections.

## 背景补充

Structured lattice schemes may expose algebraic or representation choices that matter for attack estimation and learning-assisted triage.

## 我的推断

This can support negative-cyclic modeling or block-circulant feature extraction without claiming new attacks.

## Minimum viable version

Within 2-4 weeks: read CoNAN and create a taxonomy of structure features relevant to RLWE / MLWE toy instances.

## Stronger version

Build a benchmark comparing raw vector representation, polynomial representation, and block-circulant / negative-cyclic representation for toy classification or ranking.

## Required knowledge

RLWE / MLWE structure, polynomial rings, block-circulant matrices, lattice attack estimators, ML feature design.

## Required artifacts

Feature taxonomy, toy instance generator, benchmark scripts, reproducibility README.

## Feasibility

4

## Novelty risk

3

## Implementation risk

4

## Advisor pitch

This is an intermediate step between theory and AI: before training models, define the right structured inputs.

## Why this helps 27fall PhD application

It shows the user can combine cryptographic structure and machine learning representation design.

## Next 3 actions

1. Read CoNAN introduction and framework.
2. List structure features used or implied.
3. Draft a toy RLWE / MLWE representation benchmark.

## TODO_VERIFY

- Verify CoNAN's actual framework and target.
- Verify benchmark novelty.
- Verify whether negative-cyclic representation is appropriate.

## IDEA-10D-06

## Working title

Module-SIS Chameleon Hash with Reproducible Parameterization

## Category

theory-light primitive

## Core question

Can I build a conservative Module-SIS based chameleon hash / commitment primitive artifact with correctness, collision/adaptation interface, parameter estimation, and implementation notes?

## Lattice/PQC anchor evidence

This is a user-specific candidate seed supported by the user's research profile. Recent artifacts provide indirect support through lattice primitives, BRaccoon, commitments, signatures, and module lattice assumption discussion.

## 论文事实

- No recent Top 3 paper directly constructs this primitive.
- Phase 10A identifies BRaccoon and lattice privacy primitives as secondary-watch related work.

## 背景补充

Module-SIS is a standard lattice assumption used in many lattice primitives. Chameleon hash requires a collision/adaptation mechanism and careful security goal definition.

## 我的推断

This remains the best short-term construction-oriented track, but it should be driven by a clear artifact rather than claims borrowed from MLWE attack papers.

## Minimum viable version

Within 2-4 weeks: write formal syntax, correctness condition, assumption mapping, toy parameter table, and a Python/Sage prototype stub.

## Stronger version

Workshop/submission-quality primitive note with comparison to lattice commitments, reproducible parameters, benchmark, and proof outline.

## Required knowledge

SIS / Module-SIS, commitments, chameleon hash syntax, trapdoor/adaptation mechanism, parameter estimation, proof writing.

## Required artifacts

Formal definition, parameter config, prototype, correctness tests, benchmark table, related-work map.

## Feasibility

4

## Novelty risk

4

## Implementation risk

3

## Advisor pitch

This is the clearest construction-side short paper path: small primitive, reproducible parameterization, honest limitations.

## Why this helps 27fall PhD application

It shows independent primitive design and reproducible artifact ability in lattice cryptography.

## Next 3 actions

1. Review existing lattice commitments and chameleon hashes.
2. Write syntax and security goals.
3. Create a toy parameter and correctness test plan.

## TODO_VERIFY

- Verify prior Module-SIS chameleon hash constructions.
- Verify trapdoor/adaptation feasibility.
- Verify security proof structure and parameter choices.

## IDEA-10D-07

## Working title

Lattice Commitment / Chameleon Hash / Linkable Ring Signature Connection Map

## Category

survey-plus-reproducibility

## Core question

Can I build a focused map of lattice commitments, chameleon hashes, blind signatures, and linkable ring signatures to guide primitive selection?

## Lattice/PQC anchor evidence

Phase 10A secondary-watch includes BRaccoon; reading queue includes lattice signatures, ring signatures, commitments, and privacy primitive candidates.

## 论文事实

- BRaccoon is an IACR ePrint about blind lattice signatures from Raccoon according to digest metadata.
- Identity-based revocable and linkable ring signature appears in the queue but is low priority and TODO_VERIFY.

## 背景补充

Commitments, chameleon hashes, blind signatures, ring signatures, and anonymous credentials can share proof, binding, equivocation, or anonymity design patterns.

## 我的推断

A connection map can prevent primitive drift and help decide whether Module-SIS chameleon hash should connect to credentials, redactable systems, or ring signatures.

## Minimum viable version

Within 2-4 weeks: build a table of primitives, assumptions, syntax, security goals, and implementation artifact requirements.

## Stronger version

Write a related-work survey plus a toy construction map with reusable parameter-estimation script.

## Required knowledge

Commitments, chameleon hash, lattice signatures, zero-knowledge, anonymity definitions, Module-SIS.

## Required artifacts

Survey table, bibliography, assumption map, Obsidian concept graph.

## Feasibility

5

## Novelty risk

3

## Implementation risk

2

## Advisor pitch

This is a low-risk way to make the construction track coherent before committing to a specific primitive.

## Why this helps 27fall PhD application

It demonstrates research taste and ability to organize a lattice privacy primitive agenda.

## Next 3 actions

1. Read BRaccoon abstract and construction interface.
2. List 10 related lattice primitive papers.
3. Create assumption/security-goal table.

## TODO_VERIFY

- Verify which papers are actually lattice-based.
- Verify whether chameleon hash and ring signature connections are meaningful or superficial.
- Verify novelty of any proposed map.

## IDEA-10D-08

## Working title

ML-DSA Reduction Placement Audit Checklist

## Category

implementation

## Core question

Can ML-DSA implementation audit papers be turned into a checklist for reduction placement, NTT arithmetic, and correctness conditions?

## Lattice/PQC anchor evidence

Phase 10A secondary-watch includes `When Removing Reductions Goes Wrong`, A / 100, ML-DSA / Dilithium implementation security anchored.

## 论文事实

- Digest metadata says the paper audits reduction placement in production ML-DSA implementations.
- It appears as secondary-watch and advisor-relevant implementation security material.

## 背景补充

ML-DSA / Dilithium uses modular arithmetic and NTT-based polynomial operations. Lazy reductions can be safe optimization or source of subtle bugs depending on context.

## 我的推断

This can become a practical checklist parallel to ML-KEM coin security, strengthening the PQC implementation security track.

## Minimum viable version

Within 2-4 weeks: read the paper, list reduction sites and correctness conditions, create an audit checklist without running code.

## Stronger version

Build static-analysis or test-vector checks for a small subset of implementation patterns.

## Required knowledge

ML-DSA / Dilithium, modular reduction, NTT, constant-time and correctness testing, C implementation reading.

## Required artifacts

Paper note, audit checklist, test-vector plan, optional static-analysis script.

## Feasibility

4

## Novelty risk

3

## Implementation risk

4

## Advisor pitch

This is a concrete PQC implementation security idea with clear engineering deliverables and bounded claims.

## Why this helps 27fall PhD application

It shows the user can work on standardized PQC implementation reliability, not just theory.

## Next 3 actions

1. Read the ML-DSA reduction paper.
2. Extract bug model and correctness conditions.
3. Compare with ML-KEM coin audit checklist structure.

## TODO_VERIFY

- Verify exact implementation targets.
- Verify whether any existing tool already covers the same checks.
- Verify safe reproduction scope.

## IDEA-10D-09

## Working title

PQC Parameter Estimation and Reading Triage Benchmark

## Category

benchmark

## Core question

Can recent digest metadata, source health, and ranking explanations be converted into a reproducible benchmark for PQC literature triage?

## Lattice/PQC anchor evidence

Project artifacts include source health diagnostics, ranking explanations, IACR latest/RSS recovery, and optional Semantic Scholar enrichment; recent digest focuses on lattice/PQC papers.

## 论文事实

- Phase 10A-C used digest outputs to select papers and identify false-positive risks.
- Source health caveats include arXiv timeout / rate limit and Semantic Scholar rate limit.

## 背景补充

Research triage is not cryptographic contribution by itself, but a reproducible literature pipeline can support systematic reading and artifact planning.

## 我的推断

This could be a lightweight reproducibility note if framed as infrastructure for lattice/PQC research, not as a crypto paper.

## Minimum viable version

Within 2-4 weeks: define a small fixture set, label must-read / watchlist / false positive, and evaluate ranking explanations.

## Stronger version

Build an open benchmark of lattice/PQC paper triage with source health, metadata enrichment, and false-positive controls.

## Required knowledge

PQC taxonomy, information retrieval evaluation, metadata quality, reproducibility reporting.

## Required artifacts

Fixture JSON, labels, evaluation script, import report, documentation.

## Feasibility

5

## Novelty risk

4

## Implementation risk

2

## Advisor pitch

This is not the main crypto research output, but it can support a reproducible research workflow and show engineering maturity.

## Why this helps 27fall PhD application

It demonstrates practical research infrastructure and systematic literature triage.

## Next 3 actions

1. Define a 30-paper labeled fixture from W23.
2. Mark false positives like Falcon-X and GBDT privacy paper.
3. Compare ranking explanation quality before and after manual review.

## TODO_VERIFY

- Verify this is worth time relative to crypto papers.
- Verify no private data or secrets are included.
- Verify benchmark labels are stable and fair.

## IDEA-10D-10

## Working title

Lattice/PQC-Grounded Secure Aggregation and FHE Watchlist

## Category

speculative-watch

## Core question

Which FHE / RLWE secure aggregation or privacy-preserving ML papers are actually cryptographically grounded enough to read?

## Lattice/PQC anchor evidence

W23 includes CKKS / BGV / TFHE and privacy-preserving ML items, but Phase 10A flags GBDT privacy and FHE applications as watchlist unless lattice/FHE details are explicit.

## 论文事实

- Digest includes `Practical Anonymous Two-Party Gradient Boosting Decision Tree`, CKKS/BGV/FHE papers, and FHE application papers.
- Phase 10A warns not to treat generic privacy/FL/GBDT as AI4Lattice without lattice/FHE anchors.

## 背景补充

FHE often relies on RLWE / LWE-style assumptions, but application papers may not contribute to lattice security or parameters.

## 我的推断

This can be a watchlist, not a primary track: only papers with explicit CKKS/BFV/BGV/TFHE parameters, implementation, or security estimation should enter.

## Minimum viable version

Within 2-4 weeks: create a filter checklist for FHE / secure aggregation papers: scheme, assumption, parameters, security claim, implementation detail.

## Stronger version

Write a survey-plus-reproducibility note on RLWE/FHE-grounded secure aggregation papers with parameter tables.

## Required knowledge

FHE schemes, RLWE, secure aggregation, privacy-preserving ML, parameter selection.

## Required artifacts

Watchlist, filter checklist, parameter table, paper notes.

## Feasibility

4

## Novelty risk

5

## Implementation risk

3

## Advisor pitch

This is useful only if kept narrow: it prevents generic privacy papers from consuming time while preserving truly lattice-grounded FHE leads.

## Why this helps 27fall PhD application

It can support a broader privacy-computation narrative, but should remain secondary.

## Next 3 actions

1. Label W23 FHE papers as core / application / noise.
2. Read only one CKKS/BGV implementation paper.
3. Decide whether any secure aggregation item has real RLWE parameter content.

## TODO_VERIFY

- Verify whether each paper is actually lattice/FHE grounded.
- Verify whether it contributes beyond application.
- Verify if it overlaps with existing FHE surveys.

## IDEA-10D-11

## Working title

IACR Latest-Feed Recovery and Source Health Reproducibility Note

## Category

survey-plus-reproducibility

## Core question

Can I write a reproducibility note showing how source health and latest-feed recovery affect lattice/PQC paper discovery?

## Lattice/PQC anchor evidence

The project recently recovered IACR latest/RSS behavior and identified ML-KEM 2026/1117 as a strong positive that source health issues could have delayed.

## 论文事实

- Phase 9S/9S2 context identified IACR latest/RSS recovery and latest-feed observability.
- Phase 10A used IACR 2026/1117 as a strong positive paper.

## 背景补充

Research automation quality affects which papers enter the reading queue. For fast-moving PQC topics, source reliability can change research awareness.

## 我的推断

This is a useful infrastructure note, but not a cryptography research paper unless tied to methodology and reproducibility.

## Minimum viable version

Within 2-4 weeks: write a short internal report on IACR latest-feed recovery, source health fields, and missed-paper recovery.

## Stronger version

Create a reproducible audit fixture showing how failed attempts, retry policy, and latest-feed enumeration affect digest recall.

## Required knowledge

Source health, RSS/latest feeds, test fixtures, reproducibility reporting, paper triage.

## Required artifacts

Audit fixture, source health ledger sample, report, tests.

## Feasibility

5

## Novelty risk

5

## Implementation risk

2

## Advisor pitch

This is research infrastructure, not the main paper direction. It can support my workflow and demonstrate reliability engineering.

## Why this helps 27fall PhD application

It shows disciplined tooling around research discovery, but should not replace crypto research output.

## Next 3 actions

1. Summarize the IACR 2026/1117 recovery story.
2. List source health fields that matter.
3. Decide whether to keep this as internal documentation only.

## TODO_VERIFY

- Verify exact source paths and recovery behavior from code/tests.
- Verify no generated artifacts or secrets are included.
- Verify whether this has any publication value.

## IDEA-10D-12

## Working title

Lattice-Based Registration-Based Encryption and Advanced Privacy Primitive Map

## Category

PhD-longline

## Core question

Can lattice/PQC-grounded registration-based encryption, credentials, commitments, and privacy primitives become a long-term research map?

## Lattice/PQC anchor evidence

Recent digest sections include registration-based encryption / advanced encryption primitives, lattice advanced primitives, BRaccoon, commitments, vector commitments, and privacy primitives. Hard exclusion requires lattice/PQC anchors.

## 论文事实

- Some W23 records are categorized under registration-based encryption / advanced encryption primitives and lattice advanced primitives.
- Top 3 notes do not directly cover this area.

## 背景补充

Registration-based encryption, anonymous credentials, commitments, and ring signatures can be lattice-based or non-lattice. Only lattice/PQC-grounded variants belong in this backlog.

## 我的推断

This is a long-term PhD narrative option, especially for ZK-friendly PQ privacy primitives, but not a 2-week paper unless narrowed to a single primitive and assumption.

## Minimum viable version

Within 2-4 weeks: build a literature map that keeps only lattice/PQC-grounded papers and marks all generic privacy papers as excluded.

## Stronger version

Design a small lattice commitment / credential component with explicit assumption and parameter discussion.

## Required knowledge

Lattice commitments, anonymous credentials, registration-based encryption, zero-knowledge, Module-SIS, ring signatures.

## Required artifacts

Literature map, inclusion/exclusion table, assumption map, concept graph.

## Feasibility

3

## Novelty risk

4

## Implementation risk

3

## Advisor pitch

This is a PhD-longline map rather than immediate paper. It helps position Module-SIS chameleon hash within privacy primitives.

## Why this helps 27fall PhD application

It shows the user can articulate a long-term PQ privacy primitive agenda beyond one short paper.

## Next 3 actions

1. List recent privacy primitive papers from digest.
2. Mark lattice/PQC anchored vs generic.
3. Pick one narrow primitive interface to study.

## TODO_VERIFY

- Verify which papers are lattice-based.
- Verify relation to Module-SIS and commitments.
- Verify whether registration-based encryption is feasible as a near-term topic.

# Top 5 Recommended Ideas

| Rank | Idea | Why now |
| --- | --- | --- |
| 1 | IDEA-10D-01 ML-KEM Encapsulation Coin Security Review | Fastest concrete artifact, strong recent paper support, good advisor update value |
| 2 | IDEA-10D-02 Dual-Attack Score Distribution as AI4Lattice Proxy | Best fit for AI4Lattice and attack-assistance PhD narrative |
| 3 | IDEA-10D-06 Module-SIS Chameleon Hash with Reproducible Parameterization | Best short-term construction track, aligned with existing research artifact |
| 4 | IDEA-10D-04 Swin-Guided Coordinate Selection for Sparse LWE | Strong user-profile fit, but higher experiment risk |
| 5 | IDEA-10D-08 ML-DSA Reduction Placement Audit Checklist | Good secondary implementation security artifact |

# One-Month Execution Plan

## Week 1

- Read ML-KEM coin paper and Unified Dual Attack.
- Create ML-KEM audit checklist.
- Extract score distribution features from Unified Dual Attack.

## Week 2

- Read Module Lattice Security Part IV enough to build a TODO_VERIFY claim map.
- Draft Module-SIS chameleon hash syntax and security-goal outline.
- Label W23 false positives and watchlist papers.

## Week 3

- Build tiny toy LWE / sparse LWE experiment plan for coordinate ranking.
- Create Module-SIS parameterization table.
- Prepare advisor update with two candidate short-term tracks.

## Week 4

- Choose one primary artifact: ML-KEM audit checklist or AI4Lattice toy benchmark.
- Write a 2-page project proposal.
- Decide which secondary idea becomes long-term PhD narrative support.

# Advisor Discussion Agenda

1. Should the primary short-term artifact be ML-KEM implementation audit or Module-SIS chameleon hash?
2. Is dual-attack score distribution a strong enough classical baseline for AI4Lattice?
3. How much time should be spent verifying the Module-LWE quantum attack claim?
4. Which idea has the best 2-4 week deliverable?
5. Which idea best supports 27fall PhD applications?
6. Should the Module-SIS chameleon hash artifact remain construction-focused or include implementation benchmark first?
7. Is ML-DSA reduction placement a good parallel implementation-security track?
8. Which privacy primitive directions are too broad right now?
9. What would count as a credible small workshop-style contribution?
10. How should I present TODO_VERIFY and negative results in advisor meetings?
11. Should FHE secure aggregation remain a watchlist only?
12. Which paper should become the next group-meeting topic?

# Ideas to Avoid for Now

- Generic federated learning without FHE / lattice / PQC anchor.
- Generic DP-SGD or LLM fine-tuning without cryptographic relevance.
- Generic registration-based encryption without lattice/PQC construction.
- Generic zero-knowledge or commitment without SIS / Module-SIS / lattice assumption.
- Falcon-X as PQC Falcon unless original paper explicitly concerns Falcon / FN-DSA.
- Large system-level PQ privacy platform without a small primitive or benchmark.
- Full end-to-end AI key recovery claims for real LWE / MLWE parameters.
- Treating Semantic Scholar citation metadata as a relevance or novelty authority.

# Final Recommendation

Primary short-term track：**ML-KEM randomness / encapsulation coin security review and reproducible checklist**。It has the clearest recent evidence, manageable scope, and strong advisor-update value.

Secondary track：**Dual-attack score distribution based AI4Lattice benchmark**。It is the best bridge from recent LWE papers to the user's Swin-guided / attack-assistance research line.

Long-term PhD track：**Classical-grounded AI-assisted lattice cryptanalysis plus deployable PQC implementation security**，with Module-SIS chameleon hash as a construction-side artifact.

What to do tomorrow：

1. Read the ML-KEM coin paper's abstract, threat model, and library table.
2. Read the first half of Unified Dual Attack and write down candidate score features.
3. Prepare a one-page advisor question sheet comparing IDEA-10D-01 and IDEA-10D-02.
