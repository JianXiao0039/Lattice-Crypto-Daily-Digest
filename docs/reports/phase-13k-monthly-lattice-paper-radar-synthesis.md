# Phase 13K: Monthly Lattice Paper Radar Synthesis

## Executive Summary

Phase 13K implements a manual Monthly Lattice Paper Radar Synthesis.

Decisions:

- Monthly synthesis: `monthly_synthesis_implemented`
- Monthly rationale integration: `monthly_rationale_integrated_with_limits`
- Monthly source health: `monthly_source_health_integrated_with_missing_audits`
- Production gate: `eligible_for_v0_5_monthly_rc`

The monthly command is manual-only:

```powershell
python -m lattice_digest.monthly_synthesis --month YYYY-MM
```

Phase 13K generated:

- `data/monthly/2026-06.json`
- `digests/monthly/2026-06.md`

## Phase 13J Dependency Status

Found:

- `src/lattice_digest/recommendation_rationale.py`
- Daily/Weekly rationale integration docs
- Phase 13J integration and core-invariant reports

## Existing Monthly Support

No production monthly synthesis module was found before Phase 13K. The new implementation adds `src/lattice_digest/monthly_synthesis.py` as a standalone manual module entrypoint.

## 2026-06 Generated Summary

- total unique records: 49
- class counts: A=30, B=7, C=12
- core papers listed: 12
- source-starved days: present
- missing future June daily files at generation time: 12 days, 2026-06-19 through 2026-06-30
- top directions:
  - LWE / RLWE / MLWE: 18
  - ML-KEM / ML-DSA / PQC implementation: 11
  - FHE / CKKS / lattice ZK / commitments: 9

## Implementation Files

- `src/lattice_digest/monthly_synthesis.py`
- `tests/test_monthly_synthesis.py`
- `tests/test_monthly_rationale_integration.py`
- `tests/test_monthly_source_health_summary.py`

## Core Papers

Core papers are selected from existing labels, scores, and reading-priority metadata. The module does not recompute ranking scores or alter classification semantics.

Each core paper includes:

- title;
- source;
- existing class/score;
- direction;
- problem/method/contribution;
- radar relevance;
- reading action;
- evidence basis;
- TODO_VERIFY.

## Direction Trends

Monthly trend groups are reporting lenses only:

- LWE / RLWE / MLWE
- SIS / Module-SIS
- lattice reduction / BKZ / attacks
- ML-KEM / ML-DSA / PQC implementation
- FHE / CKKS / lattice ZK / commitments
- AI-assisted lattice cryptanalysis
- other PQC / adjacent crypto

The trend lens does not change production taxonomy.

## Source Health

The monthly source-health summary aggregates daily JSON `source_health` records when available. Missing source-health evidence is listed in TODO_VERIFY.

0-record all-red days remain source-starved evidence, not proof that no relevant research existed.

## Evidence Handling

- Abstract-derived rationale is used when abstract exists.
- Conclusion-derived support is used only when a conclusion field exists.
- Title-only and metadata-only records remain low-confidence.
- Keyword hits remain supporting evidence only.
- No external LLM calls are used.

## v0.4.1 Release Relation

Phase 13K does not create, move, delete, or recreate release tags. v0.4.1 release recovery remains separately gated.

## TODO_VERIFY

- Review the generated 2026-06 monthly Markdown for readability.
- Decide later whether monthly workflow command-center integration is needed.
- Confirm CI status separately.
