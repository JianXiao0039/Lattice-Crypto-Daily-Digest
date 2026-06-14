# Phase 13H Shadow-Mode Metrics With User-Confirmed Labels

## Executive Summary

Phase 13G dependencies are present. Active package version is 0.4.1. The existing `v0.4.1` tag remains at `95215b5afe18b1f13463d03929bfe27f15788695` and was not modified.

The annotation source contains 25 records, all marked `queued_for_user`. There are 0 `user_confirmed` rows, 0 `user_corrected` rows, and 0 invalid annotations. Therefore:

- human-gold metric status: `no_human_gold_labels`;
- final precision, recall, and F1: not computed;
- shadow metric status: `shadow_metrics_not_available_no_gold`;
- annotation queue remaining: 25;
- production gate: `blocked_by_multiple_conditions`.

## Human-Gold Validation

The metrics command rereads the annotation CSV and runs the existing adjudication validation in memory. A populated gold field without `user_confirmed` or `user_corrected` is rejected. A confirmed row without a valid primary label is rejected. `multi_track` requires at least two concrete secondary tracks.

## Disagreement Analysis

The 67 unreviewed shadow records are diagnostic only:

| Category | Count |
|---|---:|
| `exact_match` | 29 |
| `primary_track_disagreement` | 25 |
| `production_labeled_shadow_irrelevant` | 11 |
| `secondary_track_disagreement` | 2 |

These counts do not establish model accuracy.

## Metrics

Shadow-vs-gold metrics: unavailable.

Production-vs-gold metrics: unavailable.

No confusion matrix with human truth is emitted. The machine-readable result uses `null` for both metric bundles instead of reporting synthetic zero scores.

## Release Relation

Phase 13H does not unblock v0.4.1. The existing CI failures and missing durable Daily evidence remain independent release blockers. Good future shadow metrics would not substitute for CI, release hygiene, or durable artifact evidence.

Current `HEAD` and `origin/main` are both `6e11c27cb197f158beff069873856eb827157058`. CI run `27487639045` for that commit failed at `Run tests` on both Ubuntu and Windows.

## Core Invariant

The paper-radar production pipeline is unchanged. The new script reads annotation and shadow audit files and writes only research-track documentation. It is not imported by Daily or Weekly workflows.

## ARS Review

Academic Research Suite was used inline in experiment-agent and academic-paper-reviewer roles. It reviewed protocol validity and overclaiming only. It did not assign labels, modify production code, become a dependency, or replace repository validation.

## Changes

- Added an isolated human-gold metrics script.
- Added focused tests for valid gold metrics, no-gold behavior, label validation, and output isolation.
- Extended the offline adjudicator to support the documented `multi_track` label contract.
- Added human-gold, disagreement, gate, release-relation, and audit documents.

## Decision

- Human-gold metrics: `no_human_gold_labels`.
- Shadow-mode metrics: `shadow_metrics_not_available_no_gold`.
- Production gate: `blocked_by_multiple_conditions`.

## Validation Results

- Python: `3.15.0b2`.
- Active package: `0.4.1`.
- Workflow doctor: pass.
- Focused Phase 13H and production-noninterference tests: 11 passed.
- Full repository suite: 532 passed.
- Release hygiene: pass with the existing non-blocking legacy generated-artifact warning.
- `git diff --check`: pass, exit code 0.
- `git diff --cached --check`: pass, exit code 0.
- Staged files: none.

## TODO_VERIFY

- User reviews at least part of the 25-row annotation queue.
- Metrics are rerun after explicit `user_confirmed` or `user_corrected` decisions.
- CI and durable Daily evidence are resolved independently of v0.5 evaluation.
