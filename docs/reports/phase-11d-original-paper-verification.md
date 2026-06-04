# Phase 11D Original Paper Verification and Section-Level Reading Plan

生成日期：2026-06-04

本报告属于公开 lattice/PQC research tooling track。它不包含 target PI email、SoP draft、PI-specific application note、funding strategy、personal PhD application tracker、personal PhD narrative 或任何 private application material。

# Executive Summary

Selected paper: **On the Secrecy of the Encapsulation Coin in ML-KEM**.

Verification status:

- IACR ePrint page accessible.
- IACR PDF accessible and downloaded under the Phase 11C artifact folder.
- IACR page metadata verified: title, authors, ePrint source, keywords, and abstract metadata.
- NIST FIPS 203 official landing page accessible.
- NIST PDF direct URL attempted in this phase returned 404, so exact standard-side section/page mapping remains TODO_VERIFY.

What was verified:

- title;
- authors;
- source / ePrint ID;
- official IACR page URL;
- official IACR PDF availability;
- abstract-level topic: ML-KEM, FIPS 203, randomness, encapsulation coin;
- IACR keywords: ML-KEM, FIPS 203, randomness, encapsulation coin.

What remains TODO_VERIFY:

- full paper section structure;
- theorem / claim structure;
- proof or experiment details;
- exact libraries and configurations discussed;
- exact ML-KEM standard references;
- exact threat model and security interpretation;
- implementation reproducibility details.

Why this matters for the ML-KEM coin-security mini-artifact:

- Phase 11C's artifact folder was named `phase-11c-mlkem-coin-security`, while Phase 11B/11C text previously followed the LWE dual-attack paper.
- Phase 11D now anchors that artifact folder to the intended ML-KEM coin-security paper using official IACR metadata.
- The original paper verification note records this correction without changing source code or making unsupported security claims.

# Source Access Log

| Source | Status | Details | TODO |
| --- | --- | --- | --- |
| IACR ePrint page `https://eprint.iacr.org/2026/1117` | accessible | HEAD status 200; page fetched; metadata observed | Continue manual reading |
| IACR PDF `https://eprint.iacr.org/2026/1117.pdf` | accessible | HEAD status 200; downloaded to `research_artifacts/phase-11c-mlkem-coin-security/original_paper/iacr-2026-1117.pdf` | Do not commit PDF unless explicitly requested later |
| Local IACR page copy | available | saved as `original_paper/iacr-2026-1117-page.html` | Treat as source snapshot; official page remains source of truth |
| NIST FIPS 203 official page `https://csrc.nist.gov/pubs/fips/203/final` | accessible | HEAD status 200 | Use page to locate final PDF / standard text manually |
| NIST FIPS 203 PDF direct URL attempted | failed | attempted `https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.203.pdf`; status 404 | TODO_VERIFY official PDF URL from NIST page |

# Verified Metadata

| Field | Verified value |
| --- | --- |
| Title | On the Secrecy of the Encapsulation Coin in ML-KEM |
| Authors | Madjid G. Tehrani; William J Buchanan; Mouad Lemoudden |
| Source | Cryptology ePrint Archive |
| ePrint ID | 2026/1117 |
| Year | 2026 |
| URL | `https://eprint.iacr.org/2026/1117` |
| PDF | `https://eprint.iacr.org/2026/1117.pdf` |
| Keywords observed | ML-KEM; FIPS 203; randomness; encapsulation coin |
| Abstract status | observed on IACR page; paraphrased only in this report |
| Section list | TODO_VERIFY from PDF manual reading |

Abstract-level summary, paraphrased:

- The IACR abstract frames ML-KEM encapsulation as drawing a fresh 32-byte coin.
- It studies how coin secrecy is protected in practice.
- It reports experimental investigation across multiple libraries and a reference.
- It explicitly says it does not claim a backdoor.

This is a paraphrase of observed metadata, not a full technical claim.

# Input Evidence Used

| Input | Status | How it was used | Limitation |
| --- | --- | --- | --- |
| `docs/reports/phase-11b-deep-reading-pack.md` | available | Used to identify mismatch between prior Phase 11B selected paper and current Phase 11D primary paper | Prior file selected the LWE dual-attack paper, so its TODO items do not directly apply |
| `notes/deep_reading/phase-11b-deep-reading-pack.md` | available | Used as prior reading-pack context | It is not about 2026/1117 |
| `docs/reports/phase-11c-reproducibility-parameter-check-mini-artifact.md` | available | Used to connect ML-KEM artifact folder and identify naming/selection mismatch | It intentionally marked ML-KEM coin fields TODO_VERIFY |
| `research_artifacts/phase-11c-mlkem-coin-security/*.md` | available | Used as Phase 11C artifact context | Files are scaffolds, not original-paper verification |
| `docs/reports/phase-11a-weekly-high-value-paper-review.md` | available | Used as recent public paper-review context; 2026/1117 was fast-skim recommendation | It did not choose 2026/1117 as deep-read |
| IACR ePrint page | available | Verified metadata and abstract-level topic | Page metadata is not enough for section-level claims |
| IACR PDF | available | Downloaded for later manual reading | Section extraction not completed in this phase |
| NIST FIPS 203 page | available | Standard-side reference entry point | Exact standard sections remain TODO_VERIFY |

# Verification Matrix

| Claim or item | Source from Phase 11B / 11C | Original paper verification status | Standard-side verification status | Result | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- |
| Paper title | Phase 11A / daily digest referenced 2026/1117; Phase 11B selected a different paper | verified on IACR page | n/a | verified | none |
| Authors | digest metadata | verified on IACR page | n/a | verified | check PDF title page |
| Abstract | digest metadata / IACR page | observed on IACR page | n/a | partially verified; paraphrased | compare with PDF abstract |
| Threat model | TODO in Phase 11C | not verified from full paper | n/a | unresolved | identify adversary, access model, library assumptions |
| Security claim | TODO in Phase 11C | not verified beyond abstract-level caution | FIPS comparison pending | unresolved | avoid overclaim |
| ML-KEM relation | digest metadata and IACR title | verified title/keywords mention ML-KEM and FIPS 203 | NIST page accessible | strong metadata-level relation | verify exact standard references |
| Coin / randomness relation | IACR title/keywords/abstract | verified topic-level relation | standard mapping pending | verified as paper topic | extract definitions and terms |
| Parameters | Phase 11C TODO | not verified | standard mapping pending | unresolved | extract parameter sets if present |
| Experiment | IACR abstract says the work answers by experiment | abstract-level only | n/a | partially observed | verify experimental setup and results in PDF |
| Proof | Phase 11C TODO | not verified | n/a | unresolved | check whether paper has proof, experiment, or both |
| Implementation relevance | digest and abstract metadata | abstract-level mentions libraries | standard mapping pending | likely relevant but not fully verified | verify libraries/configurations from PDF |
| Artifact relevance | Phase 11C artifact scaffold | original paper is now accessible | standard page accessible | artifact should shift from LWE dual-attack scaffold to ML-KEM coin-security checklist | update in future only after reading |

# 论文事实

Only directly observed facts:

- The paper is titled `On the Secrecy of the Encapsulation Coin in ML-KEM`.
- It is IACR ePrint 2026/1117.
- The authors listed by IACR are Madjid G. Tehrani, William J Buchanan, and Mouad Lemoudden.
- The IACR page keywords include ML-KEM, FIPS 203, randomness, and encapsulation coin.
- The IACR abstract frames the paper around ML-KEM encapsulation coin secrecy and practical protection of that coin.
- The IACR PDF is accessible and has been downloaded locally for manual reading.

No theorem, experiment result, parameter conclusion, implementation vulnerability, or practical security impact is asserted here beyond observed metadata.

# 背景补充

This section is background only, not a claim that the paper contains every concept.

## ML-KEM / Kyber

ML-KEM is the standardized module-lattice key encapsulation mechanism derived from Kyber. It is connected to module-lattice assumptions and is specified in NIST FIPS 203.

## KEM syntax

A KEM generally includes key generation, encapsulation, and decapsulation. Encapsulation produces a ciphertext and a shared secret; decapsulation uses the secret key to recover or derive the shared secret.

## Encapsulation randomness / coins

Many randomized cryptographic algorithms use coins or randomness. For KEMs, randomness may influence encapsulation. The exact role in ML-KEM must be checked against FIPS 203 and the paper.

## Decapsulation

Decapsulation is the operation that takes a secret key and ciphertext and derives the shared secret. Whether the paper discusses decapsulation behavior is TODO_VERIFY.

## IND-CPA / IND-CCA distinction

IND-CPA and IND-CCA are security notions for encryption/KEM-like constructions. ML-KEM standardization and transforms involve these ideas, but the paper's exact security-definition discussion is TODO_VERIFY.

## Fujisaki-Okamoto transform

FO-style transformations are common background for turning CPA-secure components into CCA-secure KEMs. Whether the paper relies on this transform must be verified from the original text.

## ML-KEM parameter sets

ML-KEM has standardized parameter sets. The paper may or may not analyze all of them. Extracting parameter-set references is a reading task.

## Relation to Module-LWE

ML-KEM is module-lattice based. However, do not infer any new Module-LWE security conclusion from this paper until the original technical content is read.

## Implementation randomness risks

Randomness misuse, predictability, test hooks, or build-time configuration can matter in cryptographic implementations. The paper's actual implementation model and evidence must be verified from the PDF.

# 我的推断

## Why coin secrecy may matter for KEM security discussions

我的推断：If an encapsulation coin determines or strongly influences the derived shared secret, then access to or predictability of that coin may affect the security story. The exact relation is paper-specific and TODO_VERIFY.

## Possible relation to ML-KEM implementation review

我的推断：The paper may be useful for an implementation-review checklist around randomness, test interfaces, build-time configuration, and FIPS validation assumptions.

## Possible relation to reproducible PQC security checklist

我的推断：This paper can be turned into a public checklist artifact that separates paper claims, standard text, library behavior, and TODO_VERIFY items.

## Possible relation to MLWE / ML-KEM / PQC standard-facing track

我的推断：The strongest research workflow value is likely standard-facing PQC implementation review, not new lattice cryptanalysis.

## Possible future artifact construction

我的推断：A safe next artifact would be a non-executable checklist first. Script design should wait until the original paper's experimental setup and legal/safety boundaries are understood.

# Section-Level Reading Plan

The actual PDF section structure has not yet been extracted. The following is a provisional section-level plan and must be replaced with actual section names after reading.

## Pass 0: Metadata and Abstract

- Reading goal: confirm title, authors, abstract, keywords, and paper scope.
- Key questions: What is the exact problem? Does the abstract make a practical claim, experimental claim, or theoretical claim?
- Symbols / definitions to extract: ML-KEM, coin, randomness, shared secret.
- Claims to verify: whether the paper states a recoverability or predictability claim.
- Parameters to record: any mention of coin length, parameter sets, libraries.
- Possible artifact impact: update `todo_verify.md`.
- Difficulty estimate: low.
- TODO_VERIFY: compare page abstract with PDF abstract.

## Pass 1: Introduction

- Reading goal: understand motivation and claimed contribution.
- Key questions: Why is coin secrecy important? What gap does the paper claim?
- Symbols / definitions to extract: coin, encapsulation, FIPS configuration, library interface.
- Claims to verify: novelty, scope, limitations.
- Parameters to record: libraries, versions, standard references.
- Possible artifact impact: decide whether checklist should be implementation-focused.
- Difficulty estimate: medium.
- TODO_VERIFY: avoid accepting practical impact claim without later sections.

## Pass 2: Preliminaries / ML-KEM Background

- Reading goal: identify how the paper defines ML-KEM and coins.
- Key questions: Does the paper quote FIPS 203? Which algorithms are referenced?
- Symbols / definitions to extract: encapsulation key, decapsulation key, ciphertext, shared secret, seed, randomness.
- Claims to verify: whether the paper's terms align with FIPS 203.
- Parameters to record: ML-KEM parameter sets if mentioned.
- Possible artifact impact: fill standard comparison checklist.
- Difficulty estimate: medium.
- TODO_VERIFY: use official FIPS 203 text.

## Pass 3: Main Technical Claim

- Reading goal: identify the main claim precisely.
- Key questions: What is reachable? Under what conditions? What is not claimed?
- Symbols / definitions to extract: recovery path, injection function, generator, reseed interface if present.
- Claims to verify: exact statement of experiment or result.
- Parameters to record: library names, build settings, configuration assumptions.
- Possible artifact impact: define artifact boundaries and non-claims.
- Difficulty estimate: medium-high.
- TODO_VERIFY: do not call it an attack unless the paper does.

## Pass 4: Security Model / Proof / Experiment

- Reading goal: determine whether evidence is proof-based, experiment-based, implementation-based, or mixed.
- Key questions: What is measured? What is controlled? What validates the conclusion?
- Symbols / definitions to extract: adversary capability, test hook, production call, FIPS validated configuration.
- Claims to verify: experimental reachability, reproducibility, limitations.
- Parameters to record: versions, platforms, configuration flags, test cases.
- Possible artifact impact: decide whether any script/checklist is safe.
- Difficulty estimate: high.
- TODO_VERIFY: no experiment claim without exact paper section.

## Pass 5: Implications / Limitations

- Reading goal: understand what the authors claim and what they explicitly do not claim.
- Key questions: Do they claim a backdoor? Do they claim practical compromise? What limitations are stated?
- Symbols / definitions to extract: limitation terms, deployment context, validated configuration.
- Claims to verify: practical impact and caveats.
- Parameters to record: affected/non-affected contexts.
- Possible artifact impact: update `artifact_scope.md`.
- Difficulty estimate: medium.
- TODO_VERIFY: avoid overstatement.

## Pass 6: Related Work and Follow-up Reading

- Reading goal: identify related randomness / KEM / implementation-security work.
- Key questions: What prior work should be read? Is Dual_EC_DRBG used only as analogy?
- Symbols / definitions to extract: related standards, prior bugs, randomness-control literature.
- Claims to verify: whether cited work supports a reproducible checklist.
- Parameters to record: references and standards.
- Possible artifact impact: build bibliography pointer list.
- Difficulty estimate: medium.
- TODO_VERIFY: bibliography extraction from PDF.

# Symbol and Definition Extraction Plan

| Symbol / term | Expected meaning | Where to find it | Why it matters | Status | TODO_VERIFY |
| --- | --- | --- | --- | --- | --- |
| ML-KEM | standardized module-lattice KEM | FIPS 203; paper preliminaries | central scheme | background | paper-specific usage |
| encapsulation key | public encapsulation input / public key equivalent | FIPS 203; paper preliminaries | public input to encapsulation | TODO_VERIFY | exact notation |
| decapsulation key | secret decapsulation input | FIPS 203; paper preliminaries | secret input boundary | TODO_VERIFY | exact notation |
| ciphertext | KEM encapsulation output component | FIPS 203; paper preliminaries | public transmitted value | TODO_VERIFY | notation and role |
| shared secret | KEM derived secret | FIPS 203; paper preliminaries | security target | TODO_VERIFY | relation to coin |
| coin | encapsulation randomness | paper title / IACR keywords | main topic | metadata verified | exact definition |
| randomness | random source / coins / generator output | IACR keywords; FIPS 203 | implementation-security focus | metadata verified | exact usage |
| seed | possible generator or derivation input | paper technical sections | may affect reproducibility | TODO_VERIFY | whether present |
| hash / XOF / PRF | possible derivation mechanisms | FIPS 203; paper | may define coin/shared secret relation | background | whether present |
| IND-CCA | KEM security notion | standards/background | security interpretation | background | paper usage |
| Module-LWE | underlying assumption family | standards/background | lattice/PQC anchor | background | paper usage |
| parameter set | ML-KEM-512/768/1024 style categories | FIPS 203; paper | reproducibility / scope | background | exact mentions |

# ML-KEM Standard Comparison Plan

Checklist:

- Identify where FIPS 203 defines key generation.
- Identify where FIPS 203 defines encapsulation.
- Identify where FIPS 203 defines decapsulation.
- Identify where randomness / coins appear in encapsulation.
- Identify whether parameter sets differ in any relevant way.
- Compare the paper's terminology to the standard's terminology.
- Compare the paper's coin / randomness statement with standard algorithm steps.
- Check whether the paper distinguishes validated FIPS configuration from non-validated deployments.
- Do not conclude a standard flaw without original paper and standard text alignment.
- Do not conclude implementation vulnerability without verifying library-specific evidence.

# Impact on Phase 11C Mini-Artifact

## `artifact_scope.md`

Current impact:

- It should eventually be updated to remove the LWE dual-attack mismatch language once the artifact fully targets 2026/1117.
- For now, `original_paper_verification.md` records the correction without rewriting the existing file.

## `parameter_checklist.md`

Current impact:

- The ML-KEM / KEM randomness checklist becomes the primary checklist for this paper.
- The LWE dual-attack checklist should be marked historical / not applicable in a future cleanup.

## `reproducibility_plan.md`

Current impact:

- The plan should shift from score-distribution extraction to paper-standard-library comparison.
- Script design remains deferred.

## `todo_verify.md`

Current impact:

- Add TODO items around coin definition, library versions, FIPS 203 algorithm references, threat model, and experiment setup.

No Phase 11C files were rewritten in this phase except adding `original_paper_verification.md`.

# Advisor Discussion Questions

## Original paper claims

1. What is the paper's exact claim about encapsulation coin secrecy?
2. Does the paper present a vulnerability, an implementation reachability result, an audit warning, or a standardization concern?
3. What does the paper explicitly say it is not claiming?
4. Which experimental observations are central, and which are supporting examples?

## ML-KEM standard comparison

5. Where exactly does FIPS 203 define encapsulation randomness?
6. How should the paper's coin terminology be mapped to FIPS 203 notation?
7. Do ML-KEM parameter sets change the relevance of the coin-security discussion?
8. Does the paper discuss validated FIPS configurations separately from ordinary deployments?

## Reproducibility artifacts

9. What is a safe first reproducibility artifact: checklist, table, or script?
10. What evidence is needed before writing any code around library behavior?

## Research-track usefulness

11. Is this best treated as PQC implementation security, standards reading, or lattice assumption background?
12. Does this direction connect meaningfully to MLWE / ML-KEM security review without overclaiming cryptanalysis?

# Next Reading Tasks

## 30-minute task

- Goal: verify metadata and PDF title page.
- Input: IACR page, downloaded PDF.
- Output: corrected metadata table.
- Validation: match IACR page and PDF first page.
- TODO_VERIFY: PDF section list.

## 2-hour task

- Goal: read abstract, introduction, and preliminaries.
- Input: downloaded PDF, FIPS 203 page.
- Output: definitions table for coin, randomness, encapsulation, shared secret.
- Validation: each definition has page/section reference.
- TODO_VERIFY: standard-side algorithm mapping.

## half-day task

- Goal: read main technical and experimental sections.
- Input: downloaded PDF.
- Output: threat model, library/configuration table, non-claims list.
- Validation: no row without paper section/page reference.
- TODO_VERIFY: reproducibility feasibility.

## 1-week task

- Goal: produce a public ML-KEM coin-security checklist artifact.
- Input: paper, FIPS 203 standard text, library documentation only if needed.
- Output: checklist, source matrix, limitations, advisor questions.
- Validation: no implementation claim without source; no experiment claim without logs.
- TODO_VERIFY: whether script design is safe and useful.

# Final Recommendation

Continue reading this paper now.

Verify first:

- PDF title page and section structure;
- coin definition;
- exact threat model;
- exact library/configuration evidence;
- relation to FIPS 203 encapsulation algorithm.

Update Phase 11C artifact after the 2-hour task:

- make ML-KEM coin-security checklist primary;
- move LWE dual-attack scaffold language to historical note or a separate artifact.

Do not design a script yet. Script design should wait until the experiment/setup section is read and safety boundaries are clear.

This paper may feed into private Phase P2 later only after verified technical facts are extracted. No private materials are written in this public Phase 11D.
