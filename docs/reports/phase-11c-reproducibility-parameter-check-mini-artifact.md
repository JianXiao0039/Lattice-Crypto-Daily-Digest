# Phase 11C Reproducibility / Parameter Check Mini-Artifact

生成日期：2026-06-04

本报告属于公开 lattice/PQC research tooling track。它不包含 target PI email、SoP draft、PI-specific application note、funding strategy、personal PhD application tracker、personal PhD narrative 或任何 private PhD application material。

# Executive Summary

Selected paper: **Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE**.

Selection source: Phase 11B selected this paper as the exact deep-read paper. Therefore Phase 11C turns that Phase 11B selection into a public reproducibility / parameter-check / reading-to-artifact scaffold.

Artifact created:

`research_artifacts/phase-11c-mlkem-coin-security/`

Important naming note:

- The requested artifact folder name contains `mlkem-coin-security`, but the Phase 11B selected paper is an LWE dual-attack paper, not the ML-KEM coin paper.
- To preserve the requested path while respecting grounding, this artifact treats ML-KEM / KEM coin-security items only as a TODO_VERIFY comparison axis.
- The core artifact target is LWE dual-attack score-distribution reading and parameter-check scaffolding.

Verified from local digest / Phase 11B metadata:

- title;
- authors;
- IACR ePrint URL;
- ranking label / score;
- reading priority;
- LWE / dual attack / lattice cryptanalysis anchor.

Still TODO_VERIFY:

- original paper abstract and PDF;
- exact definitions and theorem / claim;
- score distribution definition;
- covariance target;
- LWE parameters and whether MLWE / ML-KEM relevance is direct;
- any experiments, scripts, or implementation details.

# Input Evidence Used

| Input | Status | How used | Limitation |
| --- | --- | --- | --- |
| `docs/reports/phase-11b-deep-reading-pack.md` | available | Selected paper, metadata, deep-reading plan | Generated from digest metadata; original paper still unread |
| `notes/deep_reading/phase-11b-deep-reading-pack.md` | available | Obsidian-compatible scaffold and TODO_VERIFY list | Scaffold only, no verified proof or experiment |
| `docs/reports/phase-11a-weekly-high-value-paper-review.md` | available | Confirms selected paper as One Deep-Read Paper | Review artifact, not original paper |
| `docs/reports/phase-10d-dynamic-research-idea-backlog.md` | available | Context for AI4Lattice / reproducible security review idea seeds | Idea backlog is inference-heavy and must remain TODO_VERIFY |
| `notes/papers/*.md` | available in project | Background that related paper notes exist | Notes are scaffolds unless original papers were read |
| latest daily / weekly digest artifacts | available in project | General source-health and ranking context | Do not infer technical claims from generated ranking alone |

# Selected Paper and Artifact Target

| Field | Value |
| --- | --- |
| Title | Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE |
| Source / ID | IACR ePrint 2026/1048 |
| URL | `https://eprint.iacr.org/2026/1048` |
| Lattice/PQC anchor evidence | LWE; dual attack; covariance-based score distribution; lattice reduction / attacks |
| Artifact target | public reading-to-artifact scaffold for LWE dual-attack parameter and reproducibility checks |
| Expected value | turns a high-priority digest item into a structured checklist before deep technical reading |

# Artifact Scope

## It is

- a public reading-to-artifact scaffold;
- a parameter/security checklist;
- a reproducibility planning artifact;
- a bridge from paper triage to technical reading;
- a TODO_VERIFY container for LWE dual-attack model extraction;
- a cautious place to compare whether any result has ML-KEM / MLWE relevance after reading.

## It is not

- a completed reproduction;
- a security proof;
- an implementation result;
- an attack result;
- a claim about the paper's correctness;
- a claim that the paper affects ML-KEM;
- a claim that the artifact has run experiments;
- a private PhD application material.

# 论文事实

Only directly supported facts from Phase 11B or digest metadata:

- The selected paper title is `Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE`.
- Authors listed in local metadata: Yechen Li; Qunxiong Zheng.
- Source / ID: IACR ePrint 2026/1048.
- URL: `https://eprint.iacr.org/2026/1048`.
- Digest ranking: A / 100.
- Reading priority: 必须精读; reading_priority_score 95.
- Digest / Phase 11B anchor evidence: LWE, dual attack, covariance-based score distribution, lattice reduction / attacks.

No original-paper theorem, proof, experiment, parameter, implementation result, or security conclusion has been verified by this artifact.

# 背景补充

This section is background only. It does not claim the selected paper contains every item.

## LWE and dual attacks

LWE is a central lattice problem family. Dual attacks are a common lattice-cryptanalysis direction where the attack studies dual-side structures, distinguishers, or score behavior. For this paper, the precise dual-attack model must be extracted from the original text.

## Score distribution and covariance

The title suggests that the paper predicts score distributions using covariance-based analysis. Background interpretation: such a score might describe a distinguisher, candidate ranking value, or attack statistic. The actual definition is TODO_VERIFY.

## ML-KEM / Kyber comparison axis

ML-KEM / Kyber is a standardized module-lattice KEM. Because the selected paper is LWE-focused by title and digest metadata, any relation to ML-KEM / MLWE is TODO_VERIFY. Do not claim direct ML-KEM impact before checking the paper.

## KEM encapsulation randomness / coins

KEM encapsulation may involve randomness or coins depending on the scheme and transform. This artifact includes a coin-security checklist only because the requested artifact path names ML-KEM coin security. That checklist is a comparison scaffold, not a claim about the selected LWE dual-attack paper.

## IND-CPA / IND-CCA and FO transform

For KEM background, IND-CPA and IND-CCA security notions and transforms such as Fujisaki-Okamoto may be relevant when reading ML-KEM coin-security material. For the selected dual-attack paper, relevance is TODO_VERIFY.

# 我的推断

## Reproducible PQC security review

我的推断：The selected paper may be useful as a reproducible security-review item if it exposes parameters, score formulas, experiments, or estimator comparisons.

## LWE / MLWE parameter reading artifact

我的推断：The paper can likely be turned into a parameter extraction checklist for LWE dual attacks. Direct MLWE / ML-KEM relevance remains TODO_VERIFY.

## Possible small paper note

我的推断：A small public note could compare attack-model assumptions, score definitions, and parameter regimes across this paper and nearby W23 attack papers.

## Advisor discussion value

我的推断：This paper can motivate cautious technical questions about whether score distributions can support AI4Lattice cost proxies or coordinate-ranking labels.

# Parameter / Security Checklist

| Checklist item | What to record | Current status |
| --- | --- | --- |
| Scheme / primitive | LWE variant, KEM, signature, or other target | TODO_VERIFY |
| Randomness source | whether randomness appears in samples, secrets, errors, or protocol coins | TODO_VERIFY |
| Coin usage | whether KEM-style coins are involved | not established; TODO_VERIFY |
| Public inputs | public matrix / samples / public key / ciphertext if relevant | TODO_VERIFY |
| Secret inputs | secret vector, error, trapdoor, implementation secret if relevant | TODO_VERIFY |
| Failure mode | distinguishing failure, recovery failure, implementation failure, security bound issue | TODO_VERIFY |
| Leakage model | side channel, hints, covariance leakage, score leakage, randomness misuse | TODO_VERIFY |
| Relation to security definition | LWE hardness, IND-CPA, IND-CCA, KEM security, or estimator claim | TODO_VERIFY |
| Implementation assumption | code, library, randomness API, estimator script, experiment setup | TODO_VERIFY |
| Standard / spec reference needed | ML-KEM / FIPS 203 only if direct relation exists | TODO_VERIFY |
| Attack model | primal, dual, hybrid, distinguisher, score distribution | TODO_VERIFY |
| Parameters | dimension, modulus, samples, noise, secret distribution | TODO_VERIFY |

# Reproducibility Plan

## 2-hour artifact

- Goal: create a one-page metadata and TODO_VERIFY card.
- Required inputs: Phase 11B report, ePrint landing page, abstract.
- Expected outputs: title, authors, URL, problem statement, first TODO_VERIFY list.
- Validation method: compare extracted metadata against ePrint page.
- Risk: too shallow to support technical claims.
- TODO_VERIFY: abstract and exact contribution.

## 1-day artifact

- Goal: extract formal definitions and parameters.
- Required inputs: full paper PDF.
- Expected outputs: table of variables, parameters, score definition, covariance target.
- Validation method: every row must cite section/page in the original paper.
- Risk: formulas may require prior dual-attack references.
- TODO_VERIFY: whether the paper includes reproducible numerical examples.

## 1-week artifact

- Goal: write a reproducible LWE dual-attack model checklist.
- Required inputs: original paper, related dual-attack references, estimator background.
- Expected outputs: structured public note, assumptions table, parameter table, possible toy experiment plan.
- Validation method: no claim without paper citation; no experiment claim without logs.
- Risk: toy plan may not match the paper's real model.
- TODO_VERIFY: feasibility of safe toy parameter selection.

## 1-month artifact

- Goal: design a bounded AI4Lattice baseline map around score-distribution signals.
- Required inputs: paper details, toy LWE generator, baseline attack references, advisor feedback.
- Expected outputs: candidate feature/label map, toy benchmark plan, limitations section.
- Validation method: compare against classical baseline and state toy-to-real limits.
- Risk: high overclaim risk.
- TODO_VERIFY: label validity and relation to existing learning-assisted attack literature.

# Minimal Artifact Files Created

Folder:

`research_artifacts/phase-11c-mlkem-coin-security/`

Files:

- `README.md`: artifact overview and usage.
- `parameter_checklist.md`: checklist for LWE dual-attack parameters plus ML-KEM/KEM coin-security comparison fields marked TODO_VERIFY.
- `reproducibility_plan.md`: 2-hour, 1-day, 1-week, and 1-month artifact levels.
- `todo_verify.md`: unverified technical points.
- `artifact_scope.md`: boundaries and non-claims.

# What Requires Original Paper Reading

- definitions;
- threat model;
- theorem / claim;
- parameters;
- proof idea;
- experiment / implementation details;
- relation to ML-KEM standard if any;
- relation to prior work;
- whether the covariance analysis gives reproducible quantities;
- whether any score can be used in AI-assisted workflows.

# Advisor Discussion Questions

1. Is this paper best read as dual-attack theory, estimator improvement, or empirical attack analysis?
2. What exact LWE variant and parameter regime does it analyze?
3. Does the covariance-based score distribution challenge a common independence assumption?
4. Does it have direct relevance to MLWE or ML-KEM, or only generic LWE?
5. Is there any safe toy reproduction possible from the paper?
6. What prior dual-attack papers should be read first?
7. Can the score distribution be used as an AI4Lattice label without misrepresenting it?
8. Should the user compare this paper with sparse / hinted LWE secret recovery work?
9. Does the paper suggest any estimator-check artifact?
10. What is the most dangerous overclaim to avoid?
11. Should KEM coin-security work remain a separate artifact from this LWE dual-attack paper?
12. What minimum evidence would be needed before building a script?

# Next Actions

1. Verify original ePrint paper and PDF.
2. Read abstract and introduction.
3. Extract definitions.
4. Extract parameters and score definition.
5. Compare any MLWE / ML-KEM mention with the actual standard text only if the paper directly invokes it.
6. Decide whether to build a script/checklist artifact.
7. Update `notes/deep_reading/phase-11b-deep-reading-pack.md` or a future public note with verified facts only.

# Final Recommendation

Proceed to paper deep reading and parameter checklist refinement.

Do not start reproducibility script design until the original paper has been read and the parameter / score definitions are extracted.

Advisor discussion is useful after the 1-day artifact is complete.

Defer any ML-KEM coin-security claim for this artifact unless the selected paper directly connects to ML-KEM or KEM randomness. If the goal becomes ML-KEM encapsulation coin security, create a separate artifact around `On the Secrecy of the Encapsulation Coin in ML-KEM`.

# Safety Notes

- No business logic is changed.
- No scheduled automation is added.
- No private application materials are written.
- No secrets are touched.
