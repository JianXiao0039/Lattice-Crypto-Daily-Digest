# Cross-Operator Output Comparison Template v0.1

Use this template after Codex receives paste-back packages from DeepSeek-Claude and Kimi Code. Do not claim full parity until all three operators actually ran.

Legacy column names retained for compatibility: Check item, Codex result, DeepSeek-Claude result, Kimi Code result, Match?, Required fix, Responsible operator.

## Operator Execution Summary

| Field | Codex | DeepSeek-Claude | Kimi Code |
| --- | --- | --- | --- |
| Operator actually run: yes/no |  |  |  |
| Unavailable reason |  |  |  |
| Working directory |  |  |  |
| Shell / platform |  |  |  |
| Python version |  |  |  |
| Git status before |  |  |  |
| Git status after |  |  |  |
| Final status |  |  |  |

## Normalized Command List

Record each command exactly as normalized for comparison. A command list mismatch is `command_drift`.

| Step | Required command | Codex | DeepSeek-Claude | Kimi Code | Match? | Drift type |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `git status -sb` |  |  |  |  |  |
| 2 | `python --version` |  |  |  |  |  |
| 3 | `python -m lattice_digest.workflow doctor` |  |  |  |  |  |
| 4 | `python -m lattice_digest.workflow status` |  |  |  |  |  |
| 5 | `python -m lattice_digest.run --since 36h --output markdown,json --send none` |  |  |  |  |  |
| 6 | `python -m lattice_digest.workflow weekly --low-load --skip-hygiene` |  |  |  |  |  |
| 7 | `python -m lattice_digest.monthly_synthesis --month 2026-06` |  |  |  |  |  |
| 8 | `python scripts/probe_source_health.py --low-load` |  |  |  |  |  |
| 9 | `python scripts/verify_durable_artifacts.py --date 2026-06-15 --week 2026-W25 --month 2026-06` |  |  |  |  |  |
| 10 | `python scripts/export_reading_queue.py --latest` |  |  |  |  |  |
| 11 | `python scripts/export_obsidian_notes.py --latest` |  |  |  |  |  |
| 12 | `python scripts/audit_monthly_rationale_quality.py --latest` |  |  |  |  |  |
| 13 | `git diff --check` |  |  |  |  |  |
| 14 | `git diff --cached --check` |  |  |  |  |  |
| 15 | `git status -sb` |  |  |  |  |  |

## Artifact List

| Artifact | Codex | DeepSeek-Claude | Kimi Code | Match? | Drift type |
| --- | --- | --- | --- | --- | --- |
| Daily Markdown |  |  |  |  |  |
| Daily JSON |  |  |  |  |  |
| Weekly Markdown |  |  |  |  |  |
| Weekly JSON |  |  |  |  |  |
| Monthly Markdown |  |  |  |  |  |
| Monthly JSON |  |  |  |  |  |
| Source-health audit/probe |  |  |  |  |  |
| Reading queue export |  |  |  |  |  |
| Obsidian export |  |  |  |  |  |
| Monthly quality audit |  |  |  |  |  |

## Source-Health Classification Table

| Source | Codex | DeepSeek-Claude | Kimi Code | Match? | Drift type |
| --- | --- | --- | --- | --- | --- |
| arXiv |  |  |  |  |  |
| DBLP |  |  |  |  |  |
| IACR ePrint |  |  |  |  |  |
| Semantic Scholar |  |  |  |  |  |
| OpenAlex |  |  |  |  |  |
| Crossref |  |  |  |  |  |

## Monthly Audit Decision

| Field | Codex | DeepSeek-Claude | Kimi Code | Match? | Drift type |
| --- | --- | --- | --- | --- | --- |
| decision |  |  |  |  |  |
| pass_fail |  |  |  |  |  |
| quality_score |  |  |  |  |  |
| keyword-only regression |  |  |  |  |  |
| bilingual top-paper policy |  |  |  |  |  |
| TODO_VERIFY findings |  |  |  |  |  |
| reading action findings |  |  |  |  |  |

## Boundary Compliance Evidence

| Boundary | Codex | DeepSeek-Claude | Kimi Code | Match? | Drift type |
| --- | --- | --- | --- | --- | --- |
| Private paths avoided |  |  |  |  |  |
| Git add/commit/push/tag avoided |  |  |  |  |  |
| Tag operations avoided |  |  |  |  |  |
| Background automation avoided |  |  |  |  |  |
| Source/ranking/taxonomy changes avoided |  |  |  |  |  |
| External LLM runtime avoided |  |  |  |  |  |

## Final Report Section Completeness

Required sections:

- Operator
- Boundaries
- Commands Run
- Artifacts Generated
- Source Health
- Radar Output Quality
- Durable Artifact Status
- Failures / Warnings
- Next Recommended Operator
- Final Status

| Operator | Complete? | Missing sections | Drift type | Acceptance decision |
| --- | --- | --- | --- | --- |
| Codex |  |  |  |  |
| DeepSeek-Claude |  |  |  |  |
| Kimi Code |  |  |  |  |

## Drift Types

Use exactly these labels when applicable:

- `not_run_drift`
- `command_drift`
- `artifact_drift`
- `source_health_interpretation_drift`
- `boundary_drift`
- `report_format_drift`
- `environment_drift`
- `quality_audit_drift`

## Acceptance Decision

Allowed decisions:

- `accepted_for_fallback`
- `accepted_with_codex_review_required`
- `blocked_by_missing_operator`
- `blocked_by_command_drift`
- `blocked_by_artifact_drift`
- `blocked_by_source_health_interpretation_drift`
- `blocked_by_boundary_drift`
- `blocked_by_report_format_drift`
- `blocked_by_quality_audit_drift`
- `insufficient_evidence`
