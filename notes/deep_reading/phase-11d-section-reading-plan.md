---
type: section_reading_plan
status: scaffold
verification_status: TODO_VERIFY
source: IACR ePrint
paper_id: "2026/1117"
title: "On the Secrecy of the Encapsulation Coin in ML-KEM"
url: "https://eprint.iacr.org/2026/1117"
tags:
  - lattice_crypto
  - ML-KEM
  - Kyber
  - PQC
  - implementation_security
  - randomness
  - TODO_VERIFY
---

# Phase 11D Section-Level Reading Plan

## Paper Metadata

- Title: On the Secrecy of the Encapsulation Coin in ML-KEM
- Authors: Madjid G. Tehrani; William J Buchanan; Mouad Lemoudden
- Source: IACR ePrint 2026/1117
- URL: `https://eprint.iacr.org/2026/1117`
- PDF: `https://eprint.iacr.org/2026/1117.pdf`
- Keywords observed: ML-KEM; FIPS 203; randomness; encapsulation coin
- Verification status: original IACR page and PDF accessible; section list TODO_VERIFY

## Reading Objective

Move from digest/scaffold-level understanding to original-paper-level verification. The goal is to understand what the paper actually claims about ML-KEM encapsulation coin secrecy, what evidence it provides, and what can safely become a public reproducibility / parameter-check artifact.

## TODO_VERIFY

- PDF title page.
- Abstract vs IACR page abstract.
- Actual section titles.
- Coin definition.
- Threat model.
- Security claim.
- Experiment setup.
- Library versions and configurations.
- Relation to FIPS 203.
- Limitations and non-claims.

## Section-Level Plan

### Pass 0: Metadata and Abstract

- Goal: verify title, authors, abstract, keywords.
- Questions: What exactly is the problem? What is the stated contribution?
- Extract: coin, ML-KEM, randomness, shared secret.
- TODO_VERIFY: PDF abstract.

### Pass 1: Introduction

- Goal: identify motivation and scope.
- Questions: Why does coin secrecy matter? What is the paper not claiming?
- Extract: stated gap, claimed evidence, limitation language.
- TODO_VERIFY: contribution wording.

### Pass 2: Preliminaries / ML-KEM Background

- Goal: map paper terminology to FIPS 203 terminology.
- Questions: What are encapsulation key, decapsulation key, ciphertext, shared secret, randomness?
- Extract: notation and standard references.
- TODO_VERIFY: exact FIPS 203 algorithm references.

### Pass 3: Main Technical Claim

- Goal: find the core claim.
- Questions: What is reachable? Under what assumptions? What changes across libraries?
- Extract: threat model, access path, guard, configuration.
- TODO_VERIFY: do not call it an attack unless the paper does.

### Pass 4: Security Model / Proof / Experiment

- Goal: classify evidence type.
- Questions: Is the argument proof-based, experiment-based, implementation-based, or mixed?
- Extract: experimental setup, library list, version list, parameter set.
- TODO_VERIFY: reproducibility and safety boundary.

### Pass 5: Implications / Limitations

- Goal: record what can and cannot be concluded.
- Questions: Does the paper claim a backdoor? Does it claim practical compromise?
- Extract: explicit caveats and non-claims.
- TODO_VERIFY: practical impact.

### Pass 6: Related Work and Follow-up Reading

- Goal: identify standard and implementation references.
- Questions: What prior randomness or KEM implementation work should be read?
- Extract: FIPS 203 references, prior incidents, library docs.
- TODO_VERIFY: bibliography entries.

## Symbol Table

| Term | Expected meaning | Where to verify | Why it matters | Status |
| --- | --- | --- | --- | --- |
| ML-KEM | standardized module-lattice KEM | FIPS 203; paper preliminaries | core scheme | TODO_VERIFY |
| encapsulation key | public input to encapsulation | FIPS 203; paper | public-side input | TODO_VERIFY |
| decapsulation key | secret input to decapsulation | FIPS 203; paper | secret-side input | TODO_VERIFY |
| ciphertext | encapsulation output | FIPS 203; paper | transmitted value | TODO_VERIFY |
| shared secret | KEM secret output | FIPS 203; paper | security target | TODO_VERIFY |
| coin | encapsulation randomness | paper | main topic | TODO_VERIFY |
| randomness | source of coins | paper; standard | implementation security | TODO_VERIFY |
| seed | possible generator input | paper if present | reproducibility / predictability | TODO_VERIFY |
| hash / XOF / PRF | derivation mechanisms if present | paper; standard | coin/secret relation | TODO_VERIFY |
| IND-CCA | KEM security notion | standard/background | security interpretation | TODO_VERIFY |
| Module-LWE | lattice assumption family | standard/background | PQC anchor | TODO_VERIFY |
| parameter set | ML-KEM parameter category | FIPS 203; paper | scope | TODO_VERIFY |

## Advisor Discussion Questions

1. What is the exact coin-secrecy claim?
2. Is this a vulnerability paper, an audit note, or an implementation-hardening warning?
3. What does the paper explicitly avoid claiming?
4. Does the paper compare ordinary deployment and validated FIPS configuration?
5. Which part of FIPS 203 defines the relevant randomness?
6. How should the coin be mapped to ML-KEM notation?
7. Do parameter sets matter here?
8. What would be the safest public artifact: checklist or script?
9. What evidence is required before attempting reproduction?
10. How should this be framed without overstating practical security impact?
11. Is this useful for MLWE / ML-KEM research workflow?
12. Should implementation review be separated from cryptanalysis?

## Next Actions

1. Verify PDF title page.
2. Extract actual section names.
3. Read abstract and introduction.
4. Create definitions table with page references.
5. Compare with FIPS 203 encapsulation text.
6. Update Phase 11C artifact after verified reading.
7. Do not write code until experiment/safety boundary is clear.
