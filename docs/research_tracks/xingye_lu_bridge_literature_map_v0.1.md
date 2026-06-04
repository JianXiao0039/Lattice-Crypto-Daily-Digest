# Xingye Lu Bridge Literature Map v0.1

Status: public technical literature map.

This file is not a private target PI document. It must not contain emails, application strategy, funding notes, personal narrative, or professor-specific claims.

## Scope

The map tracks public technical literature that may connect:

- Module-SIS chameleon hash;
- lattice commitments;
- lattice-based linkable ring signatures;
- hash-then-one-way signatures;
- programmable hash functions;
- post-quantum privacy primitives;
- SIS / Module-SIS / MLWE primitive design.

## Bridge Directions

| Direction | Use for Module-SIS chameleon hash | Evidence status | Action |
| --- | --- | --- | --- |
| Commitments and chameleon hash | core definition and related work | direct papers still TODO_VERIFY | read_now |
| SIS / Module-SIS primitive construction | core assumption and parameter layer | track-level verified, paper-level TODO_VERIFY | read_now |
| Lattice trapdoor / preimage sampling | possible trapdoor/adaptation background | paper-level TODO_VERIFY | skim |
| Lattice-based linkable ring signatures | adjacent privacy/signature motivation | anchor must be verified | skim |
| Hash-then-one-way signatures | possible signature primitive bridge | concrete papers missing | backlog |
| Programmable hash functions | possible proof-programming background | generic versions excluded | watch |
| MLWE / ML-KEM / ML-DSA | standards and implementation background only | not quick-paper core | backlog |
| AI4Lattice | longline, not first construction dependency | separate track | watch |

## Candidate Topics

### Read Now

- classical chameleon hash definitions;
- lattice-based chameleon hash constructions;
- SIS / Module-SIS commitment papers;
- lattice trapdoor and preimage sampling references.

### Skim

- `BRaccoon: Concurrently Secure Blind Lattice Signatures from Raccoon`;
- `Witness Pseudorandom Functions for Vector Commitments and Applications`;
- `Improved Dual Attack and Trapdoor Sampling via Quantum Rejection Sampling`;
- `Identity-Based Revocable and Linkable Ring Signature`, only after lattice/PQC anchor verification.

### Backlog

- hash-then-one-way signature papers with lattice/PQC anchor;
- programmable hash papers with lattice/PQC anchor;
- ML-KEM / ML-DSA implementation audit papers;
- lattice privacy primitive surveys.

### Exclude

- generic ring signature without lattice/PQC anchor;
- generic hash without SIS/lattice/PQC anchor;
- generic commitment without SIS/lattice/PQC anchor;
- generic privacy / registration / blockchain / AI without lattice/PQC/HE/FHE anchor.

## Safe Language

Use:

- possible technical bridge;
- public literature map;
- TODO_VERIFY;
- adjacent lattice/PQC primitive context.

Avoid:

- PI fit;
- recruitment/funding claim;
- professor-specific statement;
- send-ready email angle;
- private application strategy.

## Weekly Bridge Output Format

| Item | Bridge direction | Lattice/PQC anchor | Use for Module-SIS paper | Verification status | Action |
| --- | --- | --- | --- | --- | --- |
| TODO | TODO | TODO | related work / proof vocabulary / parameterization | TODO_VERIFY | read_now / skim / backlog / watch / exclude |

## Non-Claims

- This map does not claim any professor-specific fact.
- This map does not prove any relation between a candidate and Module-SIS chameleon hash.
- This map does not replace original paper reading.
- This map does not change ranking, taxonomy, source ingestion, or workflow behavior.
