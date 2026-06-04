# Xingye Lu Bridge TODO_VERIFY Queue v0.1

Status: public technical TODO queue.

This queue contains no private application material.

## Professor-Specific Facts

- TODO_VERIFY current affiliation from official source before mentioning anywhere.
- TODO_VERIFY current research topics from official/public sources before writing any claim.
- TODO_VERIFY paper authorship from DBLP / official profile / paper pages before citing as professor-specific.
- TODO_VERIFY recruitment or funding only from official program pages, and do not store private strategy here.

## Linkable Ring Signatures

- Find lattice-based linkable ring signature papers.
- Verify whether each paper is lattice/PQC anchored.
- Extract assumptions: SIS, Module-SIS, LWE, MLWE, NTRU, or other.
- Check whether commitments, chameleon hash, programmable hash, or trapdoor collision appear.
- Exclude generic linkable ring signature papers without lattice/PQC anchor.

## Hash-Then-One-Way Signatures

- Find concrete hash-then-one-way signature references.
- Verify whether they are lattice/PQC relevant.
- Identify whether the hash component is programmable, trapdoor-related, or commitment-related.
- Do not use the topic as a claimed bridge until exact papers are verified.

## Programmable Hash Functions

- Find cryptographic programmable hash references.
- Verify whether any are lattice/PQC/SIS anchored.
- Reject generic programmable hash papers without lattice/PQC support.
- Extract only proof-technique vocabulary unless a construction is directly relevant.

## Commitments / Chameleon Hash

- Verify classical chameleon hash definitions.
- Verify lattice-based chameleon hash constructions.
- Verify SIS / Module-SIS commitment papers.
- Map commitment binding/hiding/equivocation to chameleon hash collision/adaptation.
- Identify what belongs in related work versus construction.

## SIS / Module-SIS Primitive Construction

- Verify Module-SIS assumption variants.
- Verify norm bounds, module rank, modulus, and parameter-estimation references.
- Avoid replacing SIS with LWE without changing the primitive/security model.
- Identify trapdoor mechanism requirements.

## MLWE / ML-KEM / ML-DSA Background

- Keep MLWE / ML-KEM / ML-DSA papers as background unless they support parameterization, implementation discipline, or proof vocabulary.
- Do not treat ML-KEM coin-security papers as direct Module-SIS chameleon hash related work.
- Use implementation audit papers only for reproducibility methodology unless a direct construction link is verified.

## AI4Lattice Longline

- Keep AI4Lattice separate from the short-term construction.
- Escalate only papers tied to LWE/RLWE/MLWE, BKZ, primal/dual/hybrid attack, coordinate selection, support recovery, or lattice cryptanalysis.
- Do not include generic AI/LLM/optimization papers.

## Required Verification Before Use

- Original paper title and source.
- Authors and year.
- Assumption and primitive.
- Security model.
- Whether the paper is lattice/PQC anchored.
- Whether it supports introduction, related work, construction, proof, parameterization, implementation, or future work.
- Whether it should be read_now, skim, backlog, watch, or exclude.
