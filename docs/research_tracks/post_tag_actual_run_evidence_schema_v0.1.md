# Post-Tag Actual Run Evidence Schema v0.1

## Purpose

This schema prevents pre-tag files, probes, and fixtures from being counted as actual post-tag automation evidence.

## Evidence Classes

Each observation must use exactly one class:

- `automation_post_tag_actual`: a named automation run started after the tag.
- `manual_post_tag_equivalent`: a manually invoked post-tag command equivalent to part of an automation workflow.
- `pre_tag_baseline`: persisted evidence created before the tag.
- `historical_ci_evidence`: CI evidence about a commit or platform, not a Daily or Weekly automation run.
- `synthetic_test_fixture`: test-only data.
- `unknown`: evidence that cannot be classified reliably.

## Required Fields

| Field | Meaning |
|---|---|
| `observation_id` | Stable local identifier |
| `date/time` | Evidence timestamp with timezone when known |
| `evidence_class` | One exact class above |
| `artifact_date` | Date represented by the artifact |
| `artifact_path` | Repository path, or `none` |
| `commit_hash` | Related commit, if verified |
| `tag_relative_status` | Before, at, or after `v0.4.0` |
| `workflow/run_identifier` | CI or automation identifier |
| `automation_name` | Named automation or manual command |
| `source_health_summary` | Available source-health evidence |
| `record_count` | Persisted or verified run count |
| `source_starved_status` | `true`, `false`, or `unknown` |
| `IACR_status` | Latest/recovery status |
| `Semantic_Scholar_status` | Enrichment status without key value |
| `validation_status` | Generated, verified, persisted, failed, or unknown |
| `confidence` | `high`, `medium`, or `low` |
| `evidence_source` | File, Git, API, or workflow metadata |
| `TODO_VERIFY` | Unresolved evidence requirement |

## Counting Rules

- Modification time alone does not prove automation execution.
- A connectivity probe is not a Daily run.
- A generated but uncommitted CI artifact proves a run attempt, not persistence.
- A manual handoff replay is not a Weekly Public Synthesis run.
- Pre-tag artifacts remain baseline evidence even when inspected after the tag.
