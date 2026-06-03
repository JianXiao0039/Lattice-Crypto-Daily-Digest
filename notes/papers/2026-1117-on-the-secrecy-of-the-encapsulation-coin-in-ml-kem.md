---
type: paper_note
status: scaffold
verification_status: TODO_VERIFY
source: digest
title: "On the Secrecy of the Encapsulation Coin in ML-KEM"
paper_id: "iacr:2026/1117"
date_seen: "2026-05-31"
priority: "must_read"
tags:
  - lattice_crypto
  - PQC
  - ML-KEM
  - Kyber
  - implementation_security
  - TODO_refine
---

# TL;DR

TODO_VERIFY：digest metadata identifies this as a directly [[ML-KEM]] / [[Kyber]] anchored implementation-security paper about encapsulation coin secrecy. It is included in the Top 3 notes because Phase 10B explicitly prioritizes this known IACR paper and because it is a strong PQC implementation security positive.

# Metadata

* Title: On the Secrecy of the Encapsulation Coin in ML-KEM
* Authors: Madjid G. Tehrani; William J Buchanan; Mouad Lemoudden
* Source: IACR ePrint
* Date seen: 2026-05-31
* URL / ID: https://eprint.iacr.org/2026/1117 / 2026/1117
* Ranking label: A
* Score: relevance_score 100; reading_priority_score 76
* Section: PQC Standards / ML-KEM / ML-DSA / Falcon; Implementation / Side-channel / Systems
* Semantic Scholar metadata: not available in inspected digest; if present later, use as advisory context only.
* Verification status: TODO_VERIFY

# Why this paper matters

Digest metadata says the paper studies secrecy of ML-KEM encapsulation coins and reports practical library-level reachability of coin recovery or predictability paths. This is directly relevant to PQC implementation hardening, reproducible audit artifacts, and the security narrative around standardized lattice KEM deployment.

# Lattice / PQC Anchor Evidence

* lattice/PQC anchor evidence: LWE/RLWE/MLWE; ML-KEM/Kyber; ML-DSA/Dilithium; PQC anchor.
* The digest abstract explicitly mentions ML-KEM, FIPS 203, encapsulation coin, OpenSSL, wolfSSL, AWS-LC, Go, Bouncy Castle, and CIRCL.

# 论文事实

## What is directly supported by the digest metadata

* Title and source are from digest metadata.
* Authors listed in digest metadata: Madjid G. Tehrani; William J Buchanan; Mouad Lemoudden.
* Source URL is IACR ePrint 2026/1117.
* Digest relevance: A / 100.
* Digest reading priority: 建议精读, reading_priority_score 76.
* Digest abstract states that ML-KEM draws a fresh 32-byte coin at encapsulation and that the paper asks how well the coin's secrecy is protected in practice.
* Digest abstract names several libraries and says coin-recovery or predictability paths are reachable under described conditions.
* TODO_VERIFY：all library behavior, threat model, FIPS configuration statements, and backdoor analogies must be checked in the original paper before reuse.

# 背景补充

## Concepts needed before reading

* [[ML-KEM]] is the standardized module-lattice KEM derived from Kyber.
* Encapsulation randomness matters because predictable or recoverable randomness can undermine KEM secrecy.
* The Fujisaki-Okamoto transform is generally relevant to KEM construction, but this note does not claim the paper discusses FO transform unless verified.
* Implementation-security papers must distinguish exploitability, test-only paths, build-time substitution, production API exposure, and validated configurations.

# 我的推断

## Relation to my research directions

* 我的推断：This paper is the strongest immediate bridge to PQC implementation security and could support a small reproducibility or audit checklist artifact.
* 我的推断：It is less central to Swin-guided lattice cryptanalysis than LWE attack papers, but it is very strong for a systems + PQC PhD narrative.
* 我的推断：It can inform how I write about standardized ML-KEM deployment risks without overclaiming cryptanalytic breaks.

# Relation to Existing Research Lines

## [[LWE]]

Indirect via module-lattice KEM security. The paper is not primarily an LWE attack paper.

## [[RLWE]]

Weak direct relation unless the paper discusses ring/module structure beyond ML-KEM implementation.

## [[MLWE]]

Relevant through ML-KEM / Kyber's module-lattice foundation.

## [[Module-SIS]]

No direct relation detected from digest metadata. Do not use it as Module-SIS chameleon hash evidence.

## [[ML-KEM]]

Core relation. The entire paper title and digest abstract are ML-KEM anchored.

## [[ML-DSA]]

Indirect PQC implementation-security relevance only.

## [[Lattice Reduction]]

No direct relation detected from digest metadata.

## [[AI-assisted lattice cryptanalysis]]

No direct relation. This is implementation security, not AI4Lattice.

## [[Module-SIS Chameleon Hash]]

No direct relation. Possible general lesson: implementation details can dominate practical security, but this is background inference only.

# Possible Use in My PhD Narrative

This paper can support a PhD narrative around deployable lattice-based cryptography: not only proving assumptions, but also auditing standardized implementations, randomness handling, and production hardening.

# Advisor Q&A Preparation

* Is this paper worth turning into a small reproduction checklist?
* Which library behavior should be manually verified first?
* Does the paper identify a vulnerability model, misuse model, or auditability gap?
* Should this become a side project parallel to Module-SIS chameleon hash?
* How should I avoid overstating implementation findings as a break of ML-KEM itself?

# Reading Plan

## First pass

Read abstract, threat model, affected libraries, and summary of coin-recovery paths.

## Second pass

Separate test-only, build-time, production-call, and validated-configuration cases.

## Deep technical pass

Build a table: library, path to coin predictability/recovery, attacker capability, reproducibility requirement, practical severity, TODO_VERIFY.

# TODO_VERIFY

* Verify authors.
* Verify abstract.
* Verify main theorem / construction / attack / experiment.
* Verify parameters.
* Verify security assumptions.
* Verify implementation details.
* Verify relation to my research idea.

# Next Actions

* Open the IACR ePrint PDF.
* Extract the library table and threat model.
* Decide whether a minimal reproduction artifact is feasible.
* Ask advisor whether ML-KEM implementation audit should be a parallel short-term thread.
