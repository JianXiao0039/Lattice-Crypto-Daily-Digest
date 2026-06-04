# Module-SIS Chameleon Hash Track

Status: public research track document.

## Purpose

Support the short-term paper target:

**A Module-SIS-Based Post-Quantum Chameleon Hash Primitive with Reproducible Parameterization and Implementation**

This track turns weekly paper radar outputs into a focused related-work, proof-sketch, parameterization, and implementation support stream.

## In-Scope

- SIS / Module-SIS / MSIS assumptions.
- Lattice commitments.
- Chameleon hashes from lattices.
- Trapdoor collision and adaptation mechanisms.
- Lattice trapdoors and gadget matrices.
- Lattice-based signatures when proof techniques or assumptions transfer.
- Linkable ring signatures only if lattice/PQC anchored.
- Rejection sampling and parameterization for lattice primitives.
- Reproducible implementations of lattice primitives.

## Out-of-Scope

- Generic hash papers.
- Generic commitment papers.
- Generic blockchain hash usage.
- Generic ZK without lattice/PQC anchor.
- Generic privacy systems without lattice/PQC anchor.
- Ring signatures without PQC/lattice relation.
- ML-KEM implementation papers unless they help parameter/security background.

## Weekly Capture Template

| Paper | Anchor | Why useful | Use for definition/proof/parameters/implementation | TODO_VERIFY |
| --- | --- | --- | --- | --- |
| TODO | SIS / Module-SIS / lattice commitment | TODO | TODO | TODO |

## Required Verification

- What is the hard assumption?
- Does the paper use SIS, Module-SIS, LWE, or another assumption?
- Is there a trapdoor?
- What property enables collision finding or adaptation?
- Is the primitive chameleon hash, commitment, signature, or adjacent?
- Are parameters explicit?
- Is there a prototype or reproducible artifact?

## Output Expectation

Each weekly synthesis should identify:

- direct construction support;
- proof / assumption support;
- parameter / implementation support;
- related-work-only papers;
- papers to exclude despite generic keyword overlap.
