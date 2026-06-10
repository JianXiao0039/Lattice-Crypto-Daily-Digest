# Weekly Handoff Non-Claims Policy v0.2

Status: public safety policy for generated weekly handoff packets.

# Core Rule

A handoff packet is a research-triage record. It is not a cryptographic, publication, professor, or implementation claim.

# Mandatory Packet Non-Claims

Every packet states:

- this is not a security proof;
- this is not a novelty claim;
- this is not a claim that the construction works;
- this is not a claim that a PI works on a topic;
- this is not a publication claim;
- this is a research triage and handoff record only.

# Module-SIS Chameleon Hash Boundary

Safe:

- candidate Module-SIS-based direction;
- feasibility study;
- possible related-work or artifact use;
- proof obligation;
- trapdoor compatibility remains TODO_VERIFY;
- toy correctness only, when supported by artifact evidence.

Unsafe:

- secure Module-SIS chameleon hash;
- complete reduction;
- real compatible trapdoor exists;
- secure/final parameters;
- novel or first construction;
- publication-ready result.

# Public Xingye Bridge Boundary

Safe:

- possible public technical bridge;
- lattice/PQC linkable-signature or programmable-hash candidate;
- no professor-specific fact asserted;
- technical relation remains TODO_VERIFY.

Unsafe:

- a PI works on the topic;
- confirmed advisor fit;
- current recruitment/funding claim;
- professor-specific application strategy;
- private email/SoP material.

# Score Boundary

Handoff scores describe triage usefulness only.

They do not measure:

- security strength;
- proof correctness;
- novelty;
- publication likelihood;
- advisor fit;
- implementation quality.

# Evidence Separation

Treat packet content as:

- observed metadata;
- deterministic policy inference;
- TODO_VERIFY;
- explicit non-claims.

Original-paper reading is required before technical claims are reused.

# Enforcement

The generator validates that every packet contains all mandatory non-claims before writing JSON or Markdown.

If a packet cannot preserve these boundaries, it should remain excluded, backlog, or TODO_VERIFY.

