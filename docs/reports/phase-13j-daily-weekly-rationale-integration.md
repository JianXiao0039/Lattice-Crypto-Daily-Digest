# Phase 13J: Daily / Weekly Rationale Integration

## Executive Summary

Phase 13J integrates the Phase 13I recommendation-rationale helper into Daily and Weekly Markdown rendering.

Decisions:

- Daily rationale integration: `daily_rationale_integrated_with_limits`
- Weekly rationale integration: `weekly_rationale_integrated_with_limits`
- Production gate: `eligible_for_v0_5_rationale_rc`

The integration is Markdown-only. Daily and Weekly JSON schemas are unchanged.

## Phase 13I Dependency Status

Found:

- `src/lattice_digest/recommendation_rationale.py`
- `tests/test_recommendation_rationale.py`
- v0.5 rationale schema, upgrade plan, integration gate, and controlled proposal docs.

## Files Inspected

- `src/lattice_digest/digest.py`
- `src/lattice_digest/weekly_synthesis.py`
- `src/lattice_digest/recommendation_rationale.py`
- `tests/test_digest_output.py`
- `tests/test_weekly_synthesis.py`
- `tests/test_recommendation_rationale.py`

## Renderer Changes

Daily:

- `_basic_paper_lines()` now renders a compact recommendation-rationale block.

Weekly:

- `_record_line()` now renders a compact rationale paragraph plus evidence basis and TODO_VERIFY caveat.

## Noninterference

Unchanged:

- source fetchers,
- source-health logic,
- ranking scores,
- ranking thresholds,
- taxonomy semantics,
- query expansion,
- negative keyword behavior,
- Daily and Weekly workflow trigger behavior,
- JSON schema.

## Evidence Handling

- Abstract-derived evidence is used when abstract exists.
- Conclusion-derived evidence is used only when conclusion text exists.
- Title-only and keyword-only records stay low-confidence.
- Keyword hits support evidence but cannot be the whole recommendation reason.

## Examples

Daily block:

> Paper problem: From the abstract, the paper studies MLWE security estimates for ML-KEM.
>
> Method / construction / attack / implementation: It proposes a hybrid attack model with lattice reduction and BKZ calibration.
>
> Evidence basis: abstract-derived; confidence=abstract_supported.

Weekly compact line:

> Rationale: From the abstract, the paper studies MLWE security estimates for ML-KEM. It is relevant because visible evidence includes MLWE, ML-KEM, and BKZ. TODO_VERIFY full proof and parameter claims.

## JSON Schema Policy

No JSON schema change in Phase 13J. Optional rationale JSON fields require a separate controlled schema patch.

## v0.4.1 Release Relation

This phase does not create, move, delete, or recreate release tags. v0.4.1 release recovery remains separately gated by CI and durable evidence status.

## TODO_VERIFY

- Review generated Daily Markdown after the next real run.
- Review generated Weekly Markdown after the next weekly synthesis.
- Decide separately whether optional JSON rationale fields are worthwhile.
