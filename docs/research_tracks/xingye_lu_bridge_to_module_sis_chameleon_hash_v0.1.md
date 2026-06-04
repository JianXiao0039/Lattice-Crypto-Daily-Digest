# Xingye Lu Bridge to Module-SIS Chameleon Hash v0.1

Status: public technical bridge-to-paper integration note.

This is not a private application document and does not contain target PI email, SoP, funding strategy, or personal narrative.

## Purpose

Define how the public Xingye Lu technical bridge track can support the short-term Module-SIS chameleon hash paper without overclaiming professor facts or drifting into private application material.

## Integration Principle

Use bridge literature only when it helps one of these public technical needs:

- related-work framing;
- motivation for lattice privacy/signature primitives;
- commitment/chameleon-hash comparison;
- proof vocabulary;
- assumption mapping;
- parameterization;
- implementation/reproducibility limitations;
- future-work positioning.

Do not use bridge literature to claim private fit, recruitment relevance, or professor-specific alignment.

## Paper Section Mapping

| Small-paper section | Bridge material allowed | What to avoid |
| --- | --- | --- |
| Introduction | post-quantum need, lattice primitive motivation, privacy/signature use cases | claiming a professor-specific motivation |
| Related Work | lattice chameleon hash, SIS commitments, lattice signatures, linkable signatures | unverified citations or generic non-lattice papers |
| Preliminaries | SIS / Module-SIS, commitments, trapdoors, chameleon hash syntax | mixing SIS and LWE as interchangeable |
| Construction | only direct technical ingredients after verification | importing signature mechanisms without proof relevance |
| Security Model | collision/adaptation notions, binding/equivocation analogies | claiming full reduction before proof |
| Parameterization | Module-SIS parameters, norm bounds, estimator inputs | production-security claims from toy parameters |
| Implementation | reproducibility manifest, toy keygen/hash/adapt/verify tests | production crypto library claims |
| Limitations / Future Work | linkable signatures, programmable hash, privacy primitives, AI4Lattice tooling as future work | private application language |

## Bridge Topic Handling

### Linkable ring signatures

Use as adjacent related work only after verifying lattice/PQC anchor. Possible role: motivate anonymous-authentication contexts where commitment or hash-like primitives may matter.

### Hash-then-one-way signatures

Use only after finding concrete papers. Possible role: proof-technique or primitive-design comparison. Do not claim relevance from the phrase alone.

### Programmable hash functions

Use only if cryptographic and preferably lattice/PQC anchored. Possible role: explain proof-programming background, not direct construction unless verified.

### Commitments and chameleon hash

This is the strongest bridge. Use to clarify:

- binding vs collision resistance;
- hiding vs privacy;
- equivocation vs trapdoor adaptation;
- commitment opening vs chameleon hash collision.

### SIS / Module-SIS primitive construction

This is the core. Keep the paper centered here:

- SIS / Module-SIS assumption;
- norm bounds;
- matrix/module dimensions;
- trapdoor mechanism;
- reproducible parameterization.

### MLWE / ML-KEM / ML-DSA

Use as background for PQC maturity and implementation discipline. Do not present standards papers as direct support for the chameleon hash construction unless a technical link is verified.

### AI4Lattice

Keep as long-term future-work or parameter/security tooling. Do not make AI part of the short-term construction unless a concrete artifact is built later.

## Recommended Small-Paper Related-Work Buckets

1. Classical chameleon hash.
2. Lattice-based chameleon hash.
3. SIS / Module-SIS commitments.
4. Lattice trapdoors and preimage sampling.
5. Lattice signatures / linkable signatures as adjacent privacy primitives.
6. Parameterization and reproducible implementation.
7. Limitations and future bridge directions.

## TODO_VERIFY Before Writing the Paper

- Identify verified lattice-based chameleon hash references.
- Identify verified SIS / Module-SIS commitment references.
- Verify any ring-signature bridge paper's lattice/PQC anchor.
- Verify whether programmable hash literature has a usable lattice/PQC component.
- Verify exact definitions and security models.
- Verify all parameter claims.
- Verify whether any bridge item belongs in future work rather than related work.

## Non-Claims

- No professor-specific fact is claimed.
- No construction is claimed secure here.
- No implementation result is claimed.
- No private application material is included.
- No ranking, taxonomy, source ingestion, or workflow behavior is changed.
