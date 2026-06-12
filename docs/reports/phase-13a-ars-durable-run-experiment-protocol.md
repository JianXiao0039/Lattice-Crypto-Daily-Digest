# Phase 13A: ARS Durable Daily Run Experiment Protocol

## Material Passport

- Workflow: `$academic-research-suite` / `experiment-agent`
- Mode: reproducibility planning and validation
- Skill version: `0.1.11`
- Evidence status: `ANALYZED`
- Engineering authority: repository tests, Git history, GitHub Actions metadata, and retained artifacts
- External runtime: disabled
- Agent team, hooks, and cross-model review: disabled

## Experiment Definition

| Field | Protocol value |
|---|---|
| Experiment ID | `DDR-<target-date>-<workflow-run-id>` |
| Run identifier | GitHub Actions run ID or explicit manual run identifier |
| Target date | Asia/Singapore date represented by the Daily artifacts |
| Run class | one exact durable-run evidence class |
| Working directory | repository root |
| Automation command | `python -m lattice_digest.run --since 36h --output markdown,json --send none --collector github_actions --quality-status provisional --run-mode daily` |
| Manual-equivalent command | same command with collector/run provenance recorded explicitly |
| Expected Markdown | `digests/<target-date>.md` |
| Expected JSON | `data/<target-date>.json` |
| Expected database | existing tracked `papers.db`, never broad force-added |
| Timeout | workflow-defined 20 minutes |

## Evidence Schema

Every observation records:

- run identifier and automation name;
- start/end timestamps;
- target date and exact command;
- evidence class;
- Markdown/JSON existence and retained paths;
- record count and source-health summary;
- source-starved status;
- IACR latest and Semantic Scholar enrichment status;
- focused/full test evidence;
- generated-artifact validation evidence;
- commit attempt/result and commit hash;
- push result and `origin/main` verification;
- Windows/Ubuntu CI run identifiers and conclusions;
- failure classification, confidence, and `TODO_VERIFY`.

## Evidence Classes

- `durable_automation_post_tag_actual`
- `durable_manual_post_tag_equivalent`
- `non_persisted_automation_post_tag_actual`
- `non_persisted_manual_post_tag_equivalent`
- `insufficient_evidence`

## Reproducibility Procedure

1. Record clean staging gate and active package version before execution.
2. Capture workflow/run ID and target Asia/Singapore date.
3. Execute the exact command without modifying source/ranking behavior.
4. Verify Markdown, JSON, and required report sections.
5. Parse JSON metadata and source-health fields; do not infer missing values.
6. Stage only the verified date-specific Markdown/JSON with the narrow workflow allowlist; stage `papers.db` normally only if already tracked and changed.
7. Record commit hash and push result.
8. Verify both exact paths in `origin/main`.
9. Link the run to Windows/Ubuntu CI evidence.
10. Assign a durable class only after all mandatory evidence is retained.

## Success Criteria

A durable run requires all nine evidence properties defined by Phase 13A. Runner-local generation without Git or an explicitly retained evidence bundle is non-persisted.

## Failure Classification

- test failure before generation;
- source-starved but retained output;
- generated-artifact validation failure;
- allowlist/staging failure;
- commit failure;
- push failure;
- origin verification failure;
- CI failure after persistence;
- insufficient evidence.

## Current Application

- Run `27327344162`: `non_persisted_automation_post_tag_actual`; generation/validation passed, commit failed.
- Run `27397762239`: `non_persisted_automation_post_tag_actual`; tests failed before generation.
- Durable post-tag Daily runs: 0.

## TODO_VERIFY

- authenticated failure log for run `27327344162`;
- first run after the narrow allowlist is published;
- retained source-health and record count for that run;
- exact origin commit and both-platform CI result.
