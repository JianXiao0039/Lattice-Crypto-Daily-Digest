# Recommendation Calibration Policy v0.1

This policy defines the deterministic recommendation calibration layer used by
the daily radar after freshness and venue metadata enrichment.

## Invariants

- Freshness remains the hard gate before primary today/new action.
- Venue and CCF metadata influence confidence only.
- Source retrieval behavior is unchanged.
- CCF ranks are never inferred from indexing sources.
- Generated or translated summary markers remain visible.

## Levels

- `Strong`: primary-fresh item with concrete user relevance and adequate evidence.
- `Medium`: useful but less urgent, indirect, or background-oriented.
- `Low`: weak or indirect relevance.
- `Backfill`: older or non-primary item with possible research value.
- `TODO_VERIFY`: insufficient evidence, missing date basis, source-health risk, or no concrete user axis.

## Score Fields

`recommendation_score` is the public action score and is capped by freshness and
risk gates. `research_value_score` preserves intrinsic research value for older
items without allowing them into primary today/new. Backfill records must not use
`Read today` as their suggested action.

The score breakdown includes:

- lattice core relevance;
- PQC standard relevance;
- cryptanalysis relevance;
- implementation/security relevance;
- AI4LC relevance;
- ZK/PQ relevance;
- venue confidence;
- source health;
- evidence completeness;
- PhD application value;
- blog or note value;
- idea generation value.

## User Relevance Axes

The calibrated reason must name concrete axes such as LWE/RLWE/MLWE, Sparse LWE,
SIS/Module-SIS, ML-KEM, ML-DSA, FN-DSA/Falcon, HAWK, lattice signatures, ring
signatures, chameleon hash, lattice cryptanalysis, BKZ/G6K, AI4LC, ZK-friendly
post-quantum primitives, or PQC implementation/security engineering.

Generic cybersecurity, generic AI, or generic privacy records must not become
`Strong` without explicit cryptography, lattice, PQC, or cryptanalysis linkage.

## Risk Flags

Risk flags are item-visible in JSON and Markdown. They include freshness routing,
missing date basis, source-health yellow/red, missing source-health linkage,
venue TODO_VERIFY, missing abstract, and missing concrete user axes.
