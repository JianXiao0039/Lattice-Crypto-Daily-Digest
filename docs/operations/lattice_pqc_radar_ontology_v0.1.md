# Lattice PQC Radar Ontology v0.1

## Purpose

This document defines the Phase 15B-04A lattice-centric PQC radar contract.
The radar remains centered on lattice cryptography. It is not a generic PQC
news feed.

## Inclusion Gate

Include an item when it has an explicit lattice scheme or lattice assumption, or
when an official standardization, migration, protocol, deployment, regulatory,
or security event directly changes the role of a lattice-based PQC scheme.

Non-lattice items require a material connection to ML-KEM, ML-DSA, FN-DSA,
HAWK, NTRU, FrodoKEM, Saber, NewHope, LWE, RLWE, MLWE, SIS, Module-SIS, NTRU
assumptions, lattice isomorphism, or MLIP.

## HAWK Disambiguation

The token `HAWK` alone is not sufficient. It must co-occur with cryptographic
context such as signature, digital signature, cryptography, post-quantum, PQC,
NIST, lattice, NTRU, MLIP, signing, verification, key generation,
cryptanalysis, specification, or security proof.

Non-cryptographic HAWK contexts are rejected, including wildlife, sports,
aircraft, missiles, radar systems, malware-detection models, graph neural
networks, computer vision, load monitoring, stock references, games, and
fictional characters.

## Dynamic Status

HAWK status is represented as dynamic metadata. The initial Phase 15B-04A
status is:

- process: NIST Additional Digital Signature Schemes
- current status: active Round 3 candidate
- round or stage: Round 3 candidate
- primary source: NIST Round 3 announcement and NIST IR 8610
- evidence tier: S0

Later official evidence may replace this status. Round 3 is not an immutable
scheme property.

## Evidence Tiers

- S0: primary authoritative. Required for standardization status changes.
- S1: primary technical. Required for cryptanalytic and technical security
  claims.
- S2: authoritative implementation. Required for production deployment claims.
- S3: reliable secondary. Mark TODO_VERIFY.
- S4: discovery only. Mark TODO_VERIFY and do not finalize current status.

## Query Contract

The Phase 15B-04A query contract is additive and disabled for production
retrieval by default. It defines only these families:

- scheme x standardization
- HAWK high precision
- scheme x migration
- scheme x protocol or PKI
- scheme x implementation security
- scheme x cryptanalysis

Each family uses:

`SCHEME_OR_LATTICE_ANCHOR AND PROCESS_OR_EVENT_ANCHOR AND CONTEXT_ANCHOR AND NOT NOISE_CONTEXT`

Academic paper sources remain separate from official status sources. An
academic API result can discover candidates, but it does not verify NIST or
government status.

## No Ranking Drift

Phase 15B-04A does not change ranking weights, thresholds, generic negative
keyword semantics, relevance labels, or reading actions. HAWK-specific
disambiguation is the only new contextual filtering contract in this batch.

## TODO_VERIFY

- Verify FN-DSA / FIPS 206 naming against current NIST status before any
  status-change publication.
- Recheck HAWK status against S0 NIST evidence during each future status update.
- Keep source-aware query production enablement deferred to a later reviewed
  batch.
