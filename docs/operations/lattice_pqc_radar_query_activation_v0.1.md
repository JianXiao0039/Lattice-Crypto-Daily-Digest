# Lattice PQC Radar Query Activation Design

This document records the Phase 15B-04B Batch 1 implementation boundary for guarded source-aware query planning.

## Contract

- Query planning is dry-run only.
- Production retrieval remains disabled by default.
- No network call is introduced by query-plan generation.
- No broad query family is globally enabled.
- Ranking, taxonomy, relevance labels, reading actions, source-health behavior, and source-starved behavior remain unchanged.

## Supported Dry-Run Mapping

- arXiv: bounded `query_groups` planning.
- DBLP: bounded `queries` planning.
- IACR ePrint: feed retrieval plus post-filter planning only.

## Disabled Or Out-Of-Scope Mapping

- OpenAlex, Crossref, and Semantic Scholar: disabled live behavior; dry-run metadata only.
- Official status sources: out of scope for Batch 1 implementation.
- Vendor/library sources: out of scope for Batch 1 implementation.

## Evidence Gates

- Standardization status requires S0 primary authoritative evidence.
- Technical security claims require S1 primary technical evidence.
- Vendor deployment claims require S2 or stronger official evidence.
- S3 and S4 sources remain TODO_VERIFY and cannot finalize current status.

## Source-Health Gates

- Source-health failures remain visible.
- Source-starved states remain explicit.
- Missing source coverage cannot be interpreted as no relevant lattice/PQC activity.

## Future Activation

Any live retrieval enablement requires a separate implementation authorization, source-health/rate-limit review, focused tests, and full-suite validation.
