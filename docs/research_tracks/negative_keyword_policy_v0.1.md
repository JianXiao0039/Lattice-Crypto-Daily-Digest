# Negative Keyword Policy v0.1

Status: public strategy document. This does not change code-level negative keyword behavior.

## Principle

Generic keywords are not enough. A paper should not be promoted into a research track unless it has a clear lattice/PQC/HE/FHE/LWE/RLWE/MLWE/SIS/Module-SIS/NTRU/ML-KEM/ML-DSA anchor.

## Downrank or Exclude Unless Anchored

- generic hash
- generic commitment
- generic ring signature
- generic registration
- generic privacy
- generic federated learning
- generic DP-SGD
- generic LLM
- generic AI
- generic optimization
- generic blockchain
- generic zero-knowledge
- generic functional encryption
- generic anonymous credential
- generic graph/image/model/code isomorphism

## Strong Exclusion Examples

- "hash" used only for blockchain or data structures.
- "commitment" without cryptographic lattice/PQC construction.
- "ring signature" without lattice/PQC or post-quantum context.
- "privacy-preserving ML" without FHE/HE/PQC/lattice anchor.
- "AI for optimization" without lattice cryptanalysis.
- "registration" without cryptographic registration-based encryption and lattice/PQC anchor.
- "isomorphism" unless lattice isomorphism or cryptographic lattice problem.

## Watchlist Handling

If a paper has some cryptographic relevance but weak lattice/PQC anchor:

- keep as watchlist;
- require TODO_VERIFY;
- do not mark as directly useful for Module-SIS chameleon hash;
- do not escalate to artifact by default.

## Re-Escalation Rule

A previously excluded paper may be re-escalated only if original paper reading confirms:

- explicit lattice/PQC/HE/FHE assumption;
- relation to LWE/RLWE/MLWE/SIS/Module-SIS/NTRU;
- standardized scheme relevance such as ML-KEM or ML-DSA;
- reproducible implementation or parameter relevance.

## Public Report Language

Use:

- "watchlist";
- "generic / insufficient lattice anchor";
- "TODO_VERIFY";
- "excluded from current track".

Avoid:

- unsupported security conclusions;
- private advisor/application language;
- claims that generic privacy/AI/hash papers are relevant without anchor.
