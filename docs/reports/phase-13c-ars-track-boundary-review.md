# Phase 13C ARS Track Boundary Review

## Review Mode

`academic-research-suite` academic-paper-reviewer guidance was applied as an auxiliary claim and boundary audit. It did not assign human gold labels or modify production logic.

## Boundary Findings

### Track A

Generic signatures, commitments, and trapdoors are too broad. Accept only when repository evidence establishes Module-SIS/SIS/lattice construction relevance.

### Track B

Author identity is not technical evidence. The experimental rule treats `Xingye Lu` as an exclusion signal to prevent name leakage. Technical ring/linkable signatures, programmable hashes, and lattice privacy primitives require an independent lattice/PQC anchor.

### Track C

Generic machine learning, time-series, and vision papers must be excluded. The paper must expose an LWE/RLWE/MLWE, lattice reduction, BKZ, primal/dual/hybrid, or coordinate-selection interface.

### Track D

This track currently behaves too much like a fallback bucket. Generic `PQC`, `post-quantum`, and `implementation` were removed as direct positive rules, but retained metadata still drives substantial over-inclusion. Human review is required before further refinement.

## Claim Review

The shadow classifier has not demonstrated higher accuracy. Current evidence supports only deterministic disagreement generation and review prioritization.
