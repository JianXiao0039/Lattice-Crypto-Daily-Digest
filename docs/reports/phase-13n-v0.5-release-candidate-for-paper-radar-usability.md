# Phase 13N v0.5 Release Candidate for Paper Radar Usability

## Executive Summary

Phase 13N prepares a v0.5 paper-radar usability release candidate. The RC verifies Daily, Weekly, Monthly, source-health, durable artifact, reading queue, Obsidian export, and recommendation-rationale usability evidence.

v0.5 RC decision: `v0_5_rc_ready_with_limits`.

Rationale quality: `rationale_quality_gate_passed_with_limits`.

Bilingual policy: `bilingual_rationale_policy_ready`.

Durable evidence: `durable_evidence_ready`.

Source health: `source_health_acceptable_for_rc`.

Production gate: `eligible_for_v0_5_rc_review`, pending external CI confirmation after submission.

## Phase 13M Dependency Status

Phase 13M output exists:

- `docs/reports/phase-13m-reading-queue-and-obsidian-export-polishing.md`
- `docs/research_tracks/v0.5_reading_queue_policy_v0.1.md`
- `docs/research_tracks/v0.5_obsidian_export_schema_v0.1.md`

The current implementation uses `lattice_digest.obsidian_scaffold`; `lattice_digest.obsidian_export` is not a project module.

## Feature Checklist

| Area | Status |
| --- | --- |
| Daily artifact | verified |
| Weekly artifact | verified |
| Monthly artifact | verified |
| Source health | acceptable for RC |
| Durable evidence | ready |
| Reading queue | ready |
| Obsidian export | ready |
| Rationale quality | passed with limits |
| Bilingual policy | documented |
| Manual-only operation | preserved |

## Rationale Quality

Monthly, reading queue, and Obsidian outputs include structured rationale. Daily/Weekly outputs remain more compact and rely on source-health, anchor evidence, and existing paper sections.

## Bilingual Policy

Bilingual rationale is recommended for A-class, Must Read, top weekly, and top monthly papers. B/C peripheral papers may remain compact Chinese-only to avoid bloated output.

## Source Health

Phase 13L diagnostic behavior is part of the RC:

- arXiv 429 is classified as rate limited.
- DBLP TLS/SSL failures are separate from generic network failure.
- Semantic Scholar key values are never printed.
- OpenAlex empty response is distinct from network failure.
- IACR failed/zero latest is not interpreted as no relevant papers.
- No anti-bot bypass is implemented.

## Durable Evidence

Representative target period:

- Daily: `2026-06-15`
- Weekly: `2026-W25`
- Monthly: `2026-06`

The RC verifier checks Markdown/JSON presence, parseability, source-health evidence, reading queue export, and Obsidian export.

## v0.4.1 Relation

v0.4.1 release clarity remains a separate maintenance/release-history issue. It should not be conflated with v0.5 usability RC evidence. v0.5 RC review can proceed as a paper-radar usability track, but final release publication still depends on CI policy and release-management decisions.

## Blockers

No local blocker is known after Phase 13N validation. External CI green status remains TODO_VERIFY after submission.

## Non-Goals

No private PhD application work, Module-SIS artifact writes, manual annotation workflows, human-gold metrics, shadow classifier productionization, source fetcher changes, ranking changes, taxonomy changes, scheduler changes, tags, or external LLM calls.
