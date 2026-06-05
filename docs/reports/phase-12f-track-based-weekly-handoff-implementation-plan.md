# Phase 12F Track-Based Weekly Handoff Implementation Plan

生成日期：2026-06-05

本报告属于公开 research tooling implementation planning。它不修改代码、现有 ranking、source ingestion、weekly workflow 或任何 private PhD application material。

# Executive Summary

Phase 12A–12E established the research-track strategy, track-based weekly report design, Module-SIS related-work radar, public Xingye Lu technical bridge map, and quick-paper handoff protocol. Phase 12F turns those documents into an implementation plan for a future weekly handoff packet generator.

This remains a planning phase. No code is changed because the current weekly synthesis is stable, deterministic, and already covered by tests. A later implementation should extend its outputs without changing source fetching, ranking thresholds, taxonomy semantics, section-classifier semantics, or existing weekly JSON/Markdown behavior.

The proposed future flow is:

1. Read existing weekly JSON.
2. Apply a separate track/handoff policy layer.
3. Produce deterministic packet drafts and exclusion records.
4. Keep all security, novelty, construction, and professor-specific claims under explicit non-claims and `TODO_VERIFY`.
5. Mirror packets into `D:\ResearchArtifacts\module-sis-chameleon-hash` only through an explicit manual option.

This helps the quick-paper project by converting general weekly discovery into concrete related-work, construction-feasibility, proof-obligation, parameterization, implementation, and comparison-table tasks.

# Input Evidence Used

| Input | Status | How used | Limitation |
| --- | --- | --- | --- |
| Phase 12A calibration report | available | Defines research tracks and hard anchoring policy | Documentation only |
| Phase 12B weekly report template | available | Defines track-first weekly sections and actions | Not implemented in code |
| Phase 12C related-work radar | available | Supplies candidate categories and noise rules | Candidate claims remain metadata-level |
| Phase 12D bridge literature map | available | Defines public technical bridge boundaries | No professor-specific fact is verified |
| Phase 12E handoff protocol | available | Defines packet schema, decision actions, and non-claims | Manual protocol only |
| `docs/research_tracks/weekly_report_template_v0.1.md` | available | Reusable weekly track layout | No current generator support |
| `docs/research_tracks/weekly_track_scoring_rubric_v0.1.md` | available | Track triage dimensions | Must remain separate from ranking |
| `docs/research_tracks/quick_paper_handoff_*.md` | available | Packet, rubric, and non-claims policies | No machine-readable schema yet |
| `src/lattice_digest/weekly_synthesis.py` | available | Current aggregation, deduplication, sections, source health, CLI, dry-run | Does not know Phase 12 tracks or handoffs |
| `src/lattice_digest/workflow.py` | available | Current manual weekly orchestration | Should not gain automatic cross-workspace writes |
| `tests/test_weekly_synthesis.py` | available | Existing deterministic/dry-run regression style | No handoff tests |
| `data/weekly/2026-W23.json` | available | Actual weekly field audit | Generated artifact; not modified |
| `data/2026-06-03.json` | available | Daily field-completeness spot check | One-day sample only |
| ResearchArtifacts RA-2 summary and feasibility matrix | available read-only | Confirms artifact intake needs: feasibility, proof, parameters, implementation | Artifact workspace not modified except optional summary |

# Current Weekly Workflow Assessment

## Current code path

- `src/lattice_digest/weekly_synthesis.py`
  - reads daily JSON;
  - supports historical list and dict payloads;
  - deduplicates by DOI, arXiv ID, URL, then normalized title;
  - preserves `seen_dates` and `seen_sources`;
  - assigns existing `research_sections` and `report_buckets`;
  - aggregates source-health summary;
  - writes stable weekly JSON and Markdown;
  - supports `--dry-run`.
- `src/lattice_digest/workflow.py`
  - invokes weekly synthesis in the manual workflow;
  - defaults weekly workflow to dry-run unless `--execute`;
  - should remain unchanged until a later explicitly approved implementation phase.

## Existing weekly JSON fields

Top-level fields observed in `data/weekly/2026-W23.json`:

- `schema_version`
- `week_id`
- `from_date`
- `to_date`
- `generated_at`
- `coverage`
- `label_counts`
- `sections`
- `report_buckets`
- `idea_bank_candidates`
- `paper_plan_candidates`
- `source_health_summary`

Record fields observed:

- identity/provenance: `paper_id`, `dedup_key`, `title`, `source`, `source_url`, `url`, DOI, arXiv ID, ePrint ID;
- metadata: `authors`, `abstract`, `venue`, `publication_date`, `year`, `seen_dates`, `seen_sources`;
- existing ranking: `relevance_label`, `relevance_score`, `ranking_explanation`, `keywords_matched`, `negative_keywords_matched`, `taxonomy_tags`;
- research workflow: `research_sections`, `report_buckets`, `research_tags`, `research_hooks`, `advisor_questions`, `why_it_matters`, `suggested_action`, reading priority fields;
- health linkage: `source_health_ref`.

Daily `2026-06-03.json` spot check:

- 20 records;
- authors and source URLs present for all 20;
- taxonomy tags, tags, ranking explanation, research sections, and source-health references present for all 20;
- DOI and arXiv IDs are sparse;
- ePrint IDs are common but not universal;
- some records lack `report_buckets`.

## Existing track information

Available but too coarse for Phase 12 handoff:

- `research_sections`, including the combined `SIS / NTRU / Commitments / Chameleon Hash` section;
- `report_buckets`, such as high priority and candidate buckets;
- taxonomy and keyword evidence;
- ranking explanation positive and negative signals.

Missing:

- explicit `module_sis_chameleon_hash` track;
- explicit public `xingye_lu_bridge` technical track;
- handoff action labels;
- handoff dimension scores;
- intended ResearchArtifacts destination;
- packet-level `TODO_VERIFY`;
- packet-level non-claims.

## Source-health caveats

Weekly JSON contains an aggregate `source_health_summary`, while individual records may contain `source_health_ref`. A future handoff generator should:

- preserve source-health caveats;
- downgrade confidence when source coverage is incomplete;
- never infer missing literature coverage from a green record alone;
- keep original-paper verification manual.

# Future Weekly Handoff Output Design

A future manual generator should create:

1. Track-based weekly synthesis summary.
2. Module-SIS chameleon hash handoff candidates.
3. Public Xingye Lu technical bridge candidates.
4. AI4Lattice watchlist candidates.
5. ML-KEM / ML-DSA background candidates.
6. Excluded/noise papers.
7. TODO_VERIFY queue.
8. Handoff packet list for ResearchArtifacts.

Suggested generated output paths:

- `exports/research-handoffs/YYYY-Www/weekly-handoff.json`
- `exports/research-handoffs/YYYY-Www/weekly-handoff.md`
- `exports/research-handoffs/YYYY-Www/packets/*.json`

These should be treated as generated artifacts and should not be committed by default.

# Handoff Field Schema

Detailed schema:

`docs/research_tracks/weekly_handoff_field_schema_v0.1.md`

Core fields:

- `handoff_id`
- `week_id`
- `source_record_id`
- `title`
- `authors_raw`
- `source`
- URL / identifier
- `track`
- `action_label`
- lattice/PQC anchor evidence
- Module-SIS relevance score
- chameleon hash relevance score
- Xingye bridge relevance score
- AI4Lattice relevance score
- implementation/reproducibility usefulness
- proof usefulness
- parameterization usefulness
- verification burden
- overclaim risk
- intended ResearchArtifacts target file
- `TODO_VERIFY`
- non-claims

Existing records can supply much of the identity, source, ranking evidence, sections, and tags. The new fields must be generated by a separate deterministic policy layer, not by changing existing relevance scores.

# Selection Logic Plan

## Hard anchoring gate

Reject generic:

- hash;
- commitment;
- registration;
- privacy;
- AI / LLM / optimization;
- blockchain;
- ZK;
- ring signature;

unless an explicit lattice/PQC/HE/FHE/LWE/RLWE/MLWE/SIS/Module-SIS/NTRU/ML-KEM/ML-DSA anchor exists.

## Module-SIS chameleon hash candidate

Require:

- explicit SIS / Module-SIS / lattice commitment / lattice trapdoor / lattice chameleon hash anchor;
- or a verified construction-adjacent primitive with a named artifact use.

Prefer:

- direct related work;
- trapdoor/adaptation mechanism;
- commitment/chameleon-hash security model;
- parameterization;
- reproducible implementation;
- comparison-table evidence.

## Public Xingye Lu bridge candidate

Require:

- public technical bridge only;
- verified lattice/PQC anchor;
- linkable signatures, hash-then-one-way signatures, programmable hash, commitments, lattice privacy primitive, or anonymous authentication relevance.

Always mark professor-specific relation as `TODO_VERIFY`. Do not generate private PI content.

## Action policy

- `handoff_now`: evidence supports a concrete artifact task and non-claims control risk.
- `handoff_after_verify`: plausible artifact use but original-paper or technical relation is unverified.
- `keep_in_radar`: relevant but no artifact task.
- `backlog`: useful background.
- `exclude`: no hard anchor or no plausible use.

# Minimal Implementation Plan

No code is changed in Phase 12F. A later Phase 12G should consider:

## Likely new module

`src/lattice_digest/weekly_handoff.py`

Responsibilities:

- read an existing weekly JSON file;
- normalize records from `sections` without duplicating them;
- apply deterministic track and handoff policy;
- emit packet JSON/Markdown;
- default to dry-run;
- never fetch sources;
- never recalculate ranking;
- never write to ResearchArtifacts unless an explicit manual mirror flag is supplied.

## Supporting policy module

Optional:

`src/lattice_digest/handoff_policy.py`

Use only if policy rules become large enough to justify separation. It should remain deterministic and explainable.

## CLI proposal

```text
python -m lattice_digest.weekly_handoff --weekly-json data/weekly/YYYY-Www.json --output-dir exports/research-handoffs --dry-run
```

Possible later opt-in:

```text
--mirror-research-artifacts D:\ResearchArtifacts\module-sis-chameleon-hash\research_radar
```

The mirror flag must:

- be manual and explicit;
- never be enabled by default weekly workflow;
- reject `PhD_Application` paths;
- write packets only, not code or paper claims.

## Existing files to inspect later

- `src/lattice_digest/weekly_synthesis.py`
- `src/lattice_digest/digest_sections.py`
- `src/lattice_digest/report_quality.py`
- `src/lattice_digest/workflow.py`
- `tests/test_weekly_synthesis.py`
- `tests/test_workflow_command_center.py`
- release-hygiene generated-artifact rules

## Backward compatibility

- Existing weekly JSON and Markdown must remain unchanged by default.
- Existing `schema_version: 1` weekly output remains valid.
- Handoff output receives its own schema version.
- No changes to fetcher, ranking, thresholds, labels, taxonomy, or source health.
- Existing manual weekly dry-run remains the default.

# Test Plan

Detailed plan:

`docs/research_tracks/weekly_handoff_test_plan_v0.1.md`

Minimum future tests:

- schema generation;
- deterministic IDs and ordering;
- Module-SIS track inclusion;
- direct chameleon hash inclusion;
- generic keyword exclusion;
- public Xingye bridge candidate remains TODO_VERIFY;
- AI4Lattice generic-AI exclusion;
- ML-KEM/ML-DSA background does not become direct handoff without concrete use;
- no PhD_Application writes;
- no secret patterns;
- dry-run writes no files;
- weekly artifact stability;
- ranking score/label unchanged;
- explicit ResearchArtifacts mirror only.

# Migration Plan

Detailed plan:

`docs/research_tracks/weekly_handoff_migration_plan_v0.1.md`

1. Template-only phase: current Phase 12 documents.
2. Manual packet phase: reviewers copy reviewed candidates into the packet template.
3. Generated packet JSON/Markdown phase: new standalone dry-run-first module.
4. Optional ResearchArtifacts sync phase: explicit manual mirror only.
5. Stable weekly handoff phase: adopt only after deterministic fixtures and boundary tests pass.

# Risk Analysis

| Risk | Impact | Control |
| --- | --- | --- |
| overfitting to current quick-paper idea | misses useful broader PQC background | preserve background/watchlist tracks |
| missing MLWE / ML-KEM papers | weak broader maturity | keep explicit background bucket |
| generic keyword pollution | noisy handoffs | hard anchoring gate and exclusion packets |
| false professor/author claims | public factual error | public technical bridge only; TODO_VERIFY; no professor facts |
| packets becoming security claims | unsafe research narrative | required non-claims and risk override |
| public/artifact boundary drift | code/proof changes from radar | separate module/output and explicit mirror |
| automatic cross-workspace writes | unexpected changes | manual explicit mirror; default dry-run |
| unstable identifiers | duplicate packets | use weekly dedup key / paper ID / identifiers with deterministic fallback |
| source-health uncertainty | false confidence | include coverage/source-health caveats |

# TODO_VERIFY

- Confirm the exact unique-record extraction method from current weekly `sections`.
- Confirm whether `dedup_key` is stable enough to serve as `source_record_id`.
- Confirm author reliability across all historical daily JSON, not only the current sample.
- Confirm whether packet drafts should include full abstracts or only short evidence.
- Confirm whether generated handoff packets should remain ignored public artifacts.
- Confirm whether ResearchArtifacts mirror should be one summary or per-packet files.
- Confirm whether all related work should be manually read before `handoff_now`.
- Confirm whether workflow integration is desirable at all; standalone CLI may be safer.

# Recommended Future Code Phase

**Phase 12G: Weekly Handoff Packet Generator v0.1**

Recommended scope:

- standalone, deterministic, dry-run-first generator;
- reads existing weekly JSON only;
- writes public generated packet drafts;
- explicit optional ResearchArtifacts mirror;
- no fetching;
- no ranking changes;
- no source-health semantic changes;
- no private workspace access.

