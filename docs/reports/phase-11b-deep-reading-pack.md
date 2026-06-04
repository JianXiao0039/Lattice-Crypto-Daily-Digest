# Phase 11B Deep Reading Pack

生成日期：2026-06-04

本报告属于公开 lattice/PQC research tooling track。它只生成 public research workflow output，不包含 target PI email、SoP draft、PI-specific application note、funding strategy、personal PhD application tracker、personal PhD narrative 或任何私有申请材料。

# Executive Summary

Selected paper: **Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE**.

This paper was selected because Phase 11A identified it as the weekly "One Deep-Read Paper". The recent weekly digest records it as an A-level paper with score 100 and reading priority score 95. Its metadata anchors it in LWE, dual attack analysis, lattice reduction / cryptanalysis, and possible ML-KEM / MLWE security-estimation context.

What it may contribute to the lattice/PQC research workflow:

- a deep-reading target for LWE dual attack modeling;
- a possible source for attack-cost proxy / score-distribution reasoning;
- a possible bridge to reproducible parameter checking;
- a possible public research note for AI-assisted lattice cryptanalysis baselines.

Still TODO_VERIFY:

- exact theorem, model, and claim scope;
- whether the analysis is proof-based, heuristic, empirical, or mixed;
- parameters and relation to ML-KEM / MLWE;
- whether any implementation or experiment is reproducible;
- whether the score distribution can be safely reused as an AI4Lattice label or feature.

# Selected Paper

| Field | Value |
| --- | --- |
| Title | Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE |
| Authors | Yechen Li; Qunxiong Zheng |
| Source / ID | IACR ePrint 2026/1048 |
| URL / identifier | `https://eprint.iacr.org/2026/1048` |
| Date seen | 2026-05-28 |
| Ranking label / score | A / 100 |
| Reading priority | 必须精读; reading_priority_score 95 |
| Source | iacr_eprint |
| Lattice/PQC anchor evidence | LWE; dual attack; covariance-based score distribution; lattice reduction / attacks; digest tags include ML-KEM and ML-DSA context |
| Why selected | Phase 11A selected it as exactly one deep-read paper because it is the strongest bridge from weekly high-value papers to LWE attack modeling and AI4Lattice baseline design |

# Input Evidence Used

| Input file | Status | How it was used | Limitation |
| --- | --- | --- | --- |
| `docs/reports/phase-11a-weekly-high-value-paper-review.md` | available | Used the "One Deep-Read Paper" decision and reading rationale | It is a generated review; it does not replace original paper reading |
| `docs/reports/phase-10b-top-3-obsidian-notes.md` | available in prior workspace context | Used only as context that deep-reading notes exist for related high-value papers | Technical details remain TODO_VERIFY |
| `notes/papers/*.md` | available in prior workspace context | Confirmed paper-note scaffolds exist for related W23 high-value papers | Notes are scaffolds, not verified paper facts |
| `digests/weekly/2026-W23.md` | available in prior workspace context | Used for W23 high-priority list and source-health context | Generated Markdown may group sections broadly |
| `data/weekly/2026-W23.json` | available in prior workspace context | Used for score, label, date seen, tags, sections, and URL | JSON metadata is not a substitute for the original paper |
| `digests/2026-06-03.md` | available in prior workspace context | Used to compare current daily priorities and source-health caveats | Daily digest covers only one day |
| `data/2026-06-03.json` | available in prior workspace context | Used for source-health context | Does not contain this paper if it was first seen earlier |
| latest newer daily / weekly artifacts | not inspected in this phase | Not needed because Phase 11A was present and explicitly selected the paper | TODO_VERIFY if future reports supersede W23 |

# What We Know from Digest Metadata

## Title

Unified Dual Attack Analyses: Covariance-Based Score Distribution Prediction for LWE

## Source

IACR ePrint.

## ID / URL

`https://eprint.iacr.org/2026/1048`

## Score / ranking label

The weekly JSON / review metadata records:

- relevance_label: A
- relevance_score: 100
- reading_priority_score: 95
- priority_label: 必须精读

## Section / category

Digest metadata places this paper in:

- LWE / RLWE / MLWE
- BKZ / LLL / G6K / Lattice Reduction / Attacks
- PQC Standards / ML-KEM / ML-DSA / Falcon

## Source health context

W23 coverage loaded 7 expected days with no missing days. The weekly summary recorded 31 unique records, including 19 A-level papers. Source health caveats from the same period include Semantic Scholar red / rate-limit style limitations and arXiv / DBLP / OpenAlex yellow degradation on some days. IACR ePrint was productive during this window.

## Semantic Scholar metadata

No Semantic Scholar metadata is relied on here. If enrichment exists elsewhere, it is advisory only and must not override reading priority or technical judgment.

# TODO_VERIFY Before Serious Reading

- Verify authors from the original paper.
- Verify abstract from the original paper.
- Verify full paper URL and PDF availability.
- Identify the main theorem / main claim.
- Identify whether the paper is primarily a construction, attack analysis, proof, experiment, or estimator-style study.
- Identify assumptions: LWE variant, secret distribution, error distribution, modulus, dimension, sample model.
- Extract parameters and whether they are close to ML-KEM / Kyber / MLWE settings.
- Identify security model and threat model.
- Verify whether the result is theoretical, empirical, implementation-oriented, or attack-oriented.
- Verify whether there are experiments, scripts, tables, or code.
- Verify whether score-distribution prediction can be used in a reproducible artifact.
- Verify what should not be generalized to real-world PQC schemes.

# 背景补充

The following is background context, not a claim that the paper contains all of these topics.

## LWE

Learning With Errors is a central lattice-based hardness assumption. Many lattice KEMs, encryption schemes, and security estimates are connected to LWE or module/ring variants. For reading this paper, the key background is the relationship between samples, secrets, error distributions, and distinguishing or recovery attacks.

## Dual attack

In lattice cryptanalysis, a dual attack typically tries to use short vectors in a dual lattice or related structure to distinguish LWE samples or recover information about the secret. The exact model varies by paper, so the first reading task is to identify what "dual attack" means here.

## Score distribution

The title suggests the paper predicts score distributions. Background interpretation: a score may measure how likely a candidate, sample, or attack event is under a given model. This must be verified from the paper; do not assume the exact definition from the title.

## Covariance

Covariance can describe dependencies between random variables. In attack analysis, covariance may matter if independence assumptions are too optimistic. TODO_VERIFY whether the paper studies dependency among attack scores, samples, coordinates, or error terms.

## ML-KEM / Kyber context

ML-KEM / Kyber is a standardized module-lattice KEM. The digest metadata tags this paper with ML-KEM context, but the original paper must be checked before claiming direct relevance to ML-KEM parameters.

## AI-assisted lattice cryptanalysis

This paper may be useful for AI-assisted lattice cryptanalysis only if its score distributions, labels, features, or cost models can be made explicit and reproducible. Background use is allowed; direct ML claims are TODO_VERIFY.

# 我的推断

## Connection to ML-KEM / Kyber security

我的推断：If the paper's LWE or MLWE parameters align with ML-KEM-like settings, it could inform security-estimation discussions. This is not established by the digest metadata alone.

## Connection to PQC implementation and reproducibility

我的推断：The paper may support a reproducible security-review note if it exposes parameters, experiments, or estimator comparisons. It is not an implementation paper by metadata alone.

## Connection to parameter/security review

我的推断：A covariance-based score distribution framework may help organize how attack assumptions affect concrete parameter review. TODO_VERIFY whether the paper gives enough numeric detail.

## Connection to possible short-term research idea

我的推断：A small public artifact could map dual attack score assumptions to a toy benchmark or reading-card format. This should be framed as literature review / reproducibility support, not as a new cryptanalytic result.

## Connection to advisor discussion

我的推断：This paper is a good candidate for asking whether a dual-attack score model can become a safe, bounded baseline for AI4Lattice coordinate ranking. It should not be described as evidence that AI can break MLWE.

# Deep Reading Plan

## Pass 1: Abstract and Introduction

Questions to answer:

- What is the problem?
- What scheme or primitive is targeted?
- What is the threat model?
- What exactly is claimed to be new?
- Why does this matter for lattice/PQC?
- What parts are unclear after first reading?
- Does the abstract mention ML-KEM, Kyber, module lattices, or only generic LWE?
- Does the paper position itself as attack analysis, estimator improvement, or theoretical probability analysis?

## Pass 2: Technical Core

Questions to answer:

- What is the formal model?
- What are the main definitions?
- What theorem or experiment supports the claim?
- What assumptions are used?
- What parameters are involved?
- Is the argument proof-based, implementation-based, attack-based, or empirical?
- What needs to be verified against the original paper?
- What exactly is the score?
- What random variables have covariance?
- Are independence assumptions challenged or refined?
- Does the paper compare against existing dual attack analyses?

## Pass 3: Research Transfer

Questions to answer:

- Can this inspire a reproducible note?
- Can this become a small implementation or parameter-check artifact?
- Does it connect to Module-SIS / MLWE / AI4Lattice?
- Does it suggest an advisor discussion question?
- Is there any short-term publishable angle?
- What should not be overclaimed?
- Can any formula, parameter table, or experiment become a stable fixture?
- Is there a safe toy benchmark that does not claim real-parameter impact?

# Symbol / Concept Table

| Symbol / concept | Likely meaning | Source | Confidence | TODO_VERIFY |
| --- | --- | --- | --- | --- |
| LWE | Learning With Errors problem family | title / digest metadata | high | Verify exact LWE variant |
| dual attack | lattice cryptanalysis method using dual-side structure | title / digest metadata | medium | Verify formal attack model |
| score distribution | distribution of attack/distinguisher scores | title inference | low-medium | Verify definition from paper |
| covariance | dependency measure among score variables or related quantities | title inference | low-medium | Verify random variables involved |
| ML-KEM | standardized module-lattice KEM context | digest tags | medium | Verify whether paper directly treats ML-KEM |
| MLWE | module LWE / possible related assumption | digest context | medium | Verify whether paper uses MLWE or only LWE |
| BKZ | lattice reduction background for attacks | research profile / digest section | low-medium | Verify whether paper uses BKZ explicitly |
| estimator | possible parameter/security review tool | background context | low | Verify whether estimator appears |
| AI4Lattice | possible downstream research workflow use | 我的推断 | low | Verify usable labels/features before any ML framing |

# Advisor Discussion Questions

1. What exact LWE or MLWE setting does this paper analyze?
2. Is the covariance-based score distribution result a proof-level improvement, a heuristic model, or an empirical observation?
3. Does the paper affect concrete ML-KEM / Kyber security interpretation, or is the relation only indirect?
4. Which assumptions in the dual attack model are most important to verify?
5. Are there parameters or examples that can be reproduced safely in a small notebook?
6. Can the score distribution be treated as a label or cost proxy for learning-assisted attack ranking, or would that distort the paper's meaning?
7. Does the result connect to sparse LWE or hinted LWE secret recovery, or is it a separate dual-attack line?
8. What should be read first to understand this paper: dual attack basics, BKZ background, or estimator literature?
9. Does the paper suggest a realistic 1-week reproducibility artifact?
10. What would be an honest boundary for saying this is relevant to AI-assisted lattice cryptanalysis?
11. Is there any connection to Module-SIS primitive security discussion, or should it remain only in the LWE/MLWE attack track?
12. What claim would be unsafe to make before fully reading the proof or experiment section?

# Possible Research Artifacts

## One 2-hour artifact

- Goal: create a one-page reading card.
- Expected output: metadata, main claimed problem, assumptions list, TODO_VERIFY list.
- Required input: abstract, introduction, digest metadata.
- Risk: may remain superficial.
- TODO_VERIFY: exact definitions and theorem statements.

## One 1-day artifact

- Goal: extract the technical model and parameter table.
- Expected output: structured table of variables, assumptions, parameters, and score definitions.
- Required input: full paper PDF.
- Risk: formulas may require more background than one day.
- TODO_VERIFY: whether parameters are comparable to ML-KEM / MLWE.

## One 1-week artifact

- Goal: write a reproducible dual-attack score-distribution review note.
- Expected output: public-safe note with definitions, parameter checklist, and possible toy experiment plan.
- Required input: original paper, related dual attack references, estimator background.
- Risk: no code or reproducible data may be available.
- TODO_VERIFY: whether a toy benchmark is technically meaningful.

## One 1-month artifact

- Goal: build a small AI4Lattice baseline map around dual attack score signals.
- Expected output: dataset specification or toy benchmark, baseline features, risk notes, comparison to classical attack assumptions.
- Required input: paper details, toy LWE generator, baseline attack scripts, careful advisor feedback.
- Risk: high overclaim risk if ML framing is too ambitious.
- TODO_VERIFY: label validity, toy-to-real limitations, relation to existing learning-assisted attack literature.

# Relation to Existing Idea Backlog

## Module-SIS chameleon hash

Relation is indirect. This paper is LWE / dual attack oriented by metadata. It may help security-assumption discussion, but it should not be used as direct evidence for Module-SIS chameleon hash construction.

## MLWE / ML-KEM / ML-DSA

Relation is potentially strong for MLWE / ML-KEM security-estimation context, but only if the original paper explicitly covers module-lattice parameters or standardized schemes. Digest tags suggest a connection; original reading must verify it.

## AI-assisted lattice cryptanalysis

Relation is promising but inferential. A score-distribution model could inspire attack-cost proxy, coordinate ranking, or label-design work. This must remain a cautious research-transfer idea until the paper's definitions are read.

## Reproducible PQC security review

This is the most plausible public artifact direction: turn the paper into a reproducible parameter / assumption / model checklist without claiming new cryptanalysis.

## Privacy / FHE

No direct relation is established from this paper's selected metadata. FHE appears in broader weekly tags for other papers, but this deep-reading pack should not force a privacy / FHE connection.

# Reading Checklist

- [ ] Verify metadata.
- [ ] Verify authors.
- [ ] Verify source URL and PDF.
- [ ] Read abstract.
- [ ] Read introduction.
- [ ] Extract definitions.
- [ ] Extract theorem / main claim.
- [ ] Extract assumptions.
- [ ] Extract parameters.
- [ ] Extract experiment / implementation evidence if present.
- [ ] Extract related work.
- [ ] Identify relation to ML-KEM / MLWE if any.
- [ ] Draft advisor questions.
- [ ] Update Obsidian-style note.
- [ ] Mark unsupported claims as TODO_VERIFY.

# Final Recommendation

Read immediately. Start with a 90-minute abstract/introduction pass, then decide whether the 3-hour deep pass should happen the same day.

Verify first:

- exact LWE variant;
- score definition;
- covariance target;
- claim type;
- parameter relevance to ML-KEM / MLWE.

Ask advisor:

- whether this paper is a good anchor for dual attack / AI4Lattice baseline reading;
- whether the score distribution can be safely translated into a reproducible toy artifact;
- what not to overclaim.

Build next:

- a public-safe one-page reading card;
- then a parameter / assumption extraction table.

Private application boundary:

- This paper may later inform Phase P2 private application materials only after manual review and only by copying verified, public-safe technical facts into the private folder.
- This Phase 11B task does not write any private application material and does not write into `D:\Code\CodexProjects\PhD_Application`.

# Safety Notes

- No source ingestion, ranking thresholds, taxonomy semantics, section classifier, query expansion, negative keywords, workflow semantics, release metadata, digest artifacts, `papers.db`, `.env`, or secrets are modified by this report.
- No scheduled automation is introduced.
- No git operation is required for this report.
