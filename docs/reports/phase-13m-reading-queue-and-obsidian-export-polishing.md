# Phase 13M Reading Queue and Obsidian Export Polishing

## Executive Summary

Phase 13M polished the local reading queue and Obsidian paper-note scaffold so Daily / Weekly / Monthly radar output is easier to act on. The change adds rationale-derived reading fields, Chinese reading actions, source-health caveats, and a structured note template.

Reading queue decision: `reading_queue_polished`.

Obsidian export decision: `obsidian_export_polished`.

No-manual-annotation gate: `no_manual_annotation_dependency_confirmed`.

Production gate: `eligible_for_v0_5_usability_rc`, subject to CI and v0.4.1 release recovery.

## Phase 13K Dependency Status

Phase 13K and Phase 13L reports were present:

- `docs/reports/phase-13k-monthly-lattice-paper-radar-synthesis.md`
- `docs/reports/phase-13l-source-health-and-durable-artifact-recovery.md`

Current generated artifacts and queue state were present:

- `state/reading-queue.json`
- `exports/obsidian-paper-notes/`
- Daily / Weekly / Monthly JSON and Markdown artifacts.

## Files Inspected

- `src/lattice_digest/reading_queue.py`
- `src/lattice_digest/obsidian_scaffold.py`
- `src/lattice_digest/recommendation_rationale.py`
- `src/lattice_digest/monthly_synthesis.py`
- `src/lattice_digest/weekly_synthesis.py`
- `docs/reading-queue.md`
- `docs/obsidian-paper-note-scaffold.md`
- `state/reading-queue.json`
- `exports/reading-queue/`
- `exports/obsidian-paper-notes/`

## Reading Queue Implementation Status

The reading queue now adds optional, backward-compatible fields:

- `paper_id`
- `authors`
- `source`
- `date`
- `score`
- `class_label`
- `reading_priority_score`
- `reading_action`
- `direction_tags`
- `radar_track`
- rationale fields
- source-health context
- first/last seen fields
- Daily/Weekly/Monthly seen fields

No existing ranking field is replaced.

## Obsidian Export Implementation Status

Paper notes now default to `status: unread` and include:

1. Radar Recommendation
2. Paper Work Summary
3. Relevance to My Research
4. Reading Checklist
5. TODO_VERIFY
6. Links

`scripts/export_obsidian_notes.py --latest` refreshes only notes created by `lattice_digest.obsidian_scaffold`. Manual notes without the generated marker are skipped.

## Reading Action Policy Summary

- `精读`: high-confidence A-class core lattice/PQC evidence.
- `扫读`: relevant but less central.
- `暂存`: peripheral or low-confidence but possibly useful.
- `忽略`: weak/irrelevant evidence.

The action is an explanation layer and does not change score/order semantics.

## Rationale Integration

Reading queue records include:

- problem summary;
- method summary;
- contribution summary;
- radar relevance;
- caveat;
- evidence basis;
- TODO_VERIFY.

Title-only and metadata-only papers retain caveats and do not receive invented method/contribution claims.

## Sample Reading Queue Record

```json
{
  "title": "Advancing Pseudorandom Codes: Beyond Parity Checks and Standard-Model CCA1 Security",
  "class_label": "A",
  "score": 100,
  "reading_priority_score": 85,
  "reading_action": "精读",
  "radar_track": "LWE / RLWE / MLWE",
  "evidence_basis": ["abstract-derived", "repository-note-derived", "metadata-derived"],
  "first_seen": "2026-06-13",
  "last_seen": "2026-06-13",
  "seen_in_daily": ["2026-06-13"],
  "seen_in_weekly": ["2026-W25"]
}
```

## Sample Obsidian Note Scaffold

```markdown
## 1. Radar Recommendation

### Why this paper appeared

- Source: iacr_eprint
- Class / score: A / 100
- Queue priority: HIGH
- Evidence basis: abstract-derived, metadata-derived, repository-note-derived

### Why read / skim / track / ignore

- Reading action: 精读
- Recommendation: 与格密码/PQC 雷达相关：可见证据包含 lwe、mlwe、module sis、module-sis、ntru、rlwe、sis。
```

## Noninterference

Ranking, scoring, ordering semantics, source fetchers, source-health logic, taxonomy, queries, negative keywords, and Daily/Weekly/Monthly trigger behavior were not changed.

## Validation

- Focused tests: `34 passed`.
- Reading queue latest export: total 65 records.
- Obsidian notes export: selected 33, refreshed 33 generated notes.

## v0.4.1 Release Relation

This phase improves usability outputs only. It does not create or move tags and does not resolve any v0.4.1 release gate by itself.

## TODO_VERIFY

- Review future Daily / Weekly / Monthly outputs for richer source abstracts.
- Decide later whether `seen_in_monthly` should be populated directly from monthly JSON records.
- Keep generated exports out of release commits unless explicitly selected.
