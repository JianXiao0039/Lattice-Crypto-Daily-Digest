# Durable Post-Tag Evidence Schema v0.2

## Classes

- `durable_automation_post_tag_actual`
- `durable_manual_post_tag_equivalent`
- `non_persisted_automation_post_tag_actual`
- `non_persisted_manual_post_tag_equivalent`
- `insufficient_evidence`

## Required Fields

| Field | Requirement |
|---|---|
| `run_identifier` | Stable automation or manual ID |
| `automation_name` | Exact workflow/operation name |
| `start_time`, `end_time` | Zoned or UTC timestamps |
| `target_date` | Artifact date in Asia/Singapore |
| `run_class` | One exact class above |
| `exact_command` | Executed command |
| `markdown_path`, `json_path` | Portable repository paths |
| `record_count` | Integer or `TODO_VERIFY` |
| `source_health` | Green/yellow/red and source-starved evidence |
| `iacr_status` | Observed state or unknown |
| `semantic_scholar_status` | Observed state without key value |
| `validation_result` | Tests and artifact checks |
| `commit_result`, `commit_hash` | Git persistence evidence |
| `push_result` | Remote publication evidence |
| `origin_main_result` | Exact path verification |
| `ci_evidence` | Run IDs and platform conclusions |
| `failure_classification` | Explicit failure stage |
| `confidence` | High/medium/low |
| `TODO_VERIFY` | Missing evidence |

## Durable Rule

All required durable properties must be affirmative. A missing commit, retained evidence bundle, origin verification, or unambiguous run type prevents a durable classification.
