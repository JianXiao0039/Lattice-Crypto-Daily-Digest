# Phase 13A: v0.4.1 Corrective Release Validation and First Durable Post-Tag Evidence

## Executive Summary

`$academic-research-suite` version 0.1.11 was available and used inline for experiment-agent reproducibility planning. Full runtime, agent teams, hooks, and cross-model review remained disabled.

The initial staging hard gate passed. Active package versions are `0.4.1`, `v0.4.0` remains unchanged, portable paths and strict doctor pass locally, and release hygiene passes. A narrow Daily publication contract now force-adds only the verified date-specific Markdown/JSON pair and stages the already tracked `papers.db` without force.

No durable post-tag Daily evidence exists. Run `27327344162` generated and validated but failed persistence. Run `27397762239` failed tests before generation. Current origin/main CI is red on both Ubuntu and Windows because the complete local hotfix has not been published.

Tag decision: `blocked_by_multiple_conditions`. v0.5 production changes remain blocked.

## Skill Use

- `experiment-agent`: evidence-schema and reproducibility protocol review;
- `academic-paper-reviewer`: performed after engineering evidence was assembled;
- no ARS code execution, repository automation, hooks, agent teams, or external API/model review.

## Version and Tag

| Item | Result |
|---|---|
| Active package version | `0.4.1` |
| Version sources | pyproject, source package, bridge package agree |
| Historical tag | `v0.4.0` |
| Historical target | `08c5f07967739ecd008773c4b167cd736848df88` |
| Historical package version | `0.3.3` |
| Tag modified | no |

## Regression Status

- Reliability artifact fields use repository-relative POSIX paths.
- Missing artifact fields remain `None`.
- `Asia/Singapore` is healthy and critical.
- Strict doctor retains genuine critical failures but ignores unrelated staging state.

## Generated-Artifact Persistence Solution

Selected solution: narrow explicit force-add.

```sh
git add -f -- "$markdown_path" "$json_path"
git add -- papers.db
```

The paths are derived from the validated run date. No directory, wildcard, database, cache, export, note, or private path is force-added. Release hygiene is unchanged for normal release commits.

## Durable Evidence Review

| Run | Classification | Reason |
|---|---|---|
| `27327344162` | `non_persisted_automation_post_tag_actual` | generated/validated; commit failed; no retained files |
| `27397762239` | `non_persisted_automation_post_tag_actual` | tests failed before generation |

Durable run count: 0. Origin/main contains neither 2026-06-11 nor 2026-06-12 Daily artifacts.

## CI Status

- Historical run `27388260673`: Ubuntu and Windows passed.
- Current origin/main run `27399295488`: Ubuntu and Windows failed at tests.
- Clean-archive reproduction of `2ee4ee3`: five failures, including stale release docs/tests and Windows path serialization.
- Current local working-tree tests are authoritative only for the uncommitted patch.

## Release Decision

`blocked_by_multiple_conditions`

Required before tagging:

1. publish the complete corrective patch through a separately approved Git operation;
2. obtain green Ubuntu and Windows CI;
3. observe one durable post-tag Daily run using the narrow allowlist;
4. verify exact Markdown/JSON paths and commit in origin/main;
5. retain source-health and CI traceability.

## v0.5 Gate

Offline design remains allowed. Production classification changes remain blocked. No production research semantics changed in Phase 13A.

## Validation Results

| Check | Result |
|---|---|
| Reliability baseline regression | 2 passed |
| Workflow command-center regression | 21 passed |
| Durable submission and workflow tests | 12 passed |
| v0.4.1 verifier tests | 4 passed |
| Repository test helper | 471 passed |
| Release hygiene | passed; legacy tracked-generated warning remains non-blocking |
| Candidate verifier | local checks passed; tag decision remains `blocked_by_multiple_conditions` |
| GitHub Actions | current run `27399295488` failed at `Run tests` on Ubuntu and Windows |
| Failed CI log text | unavailable because `gh` is unauthenticated; `TODO_VERIFY` |
| Staging gate | no staged files |

`git diff --check` and final `git status -sb` are reported after the documentation update. Local success applies only to the current uncommitted working tree.

## TODO_VERIFY

- authenticated failed logs;
- CI result after publication;
- first narrow-allowlist Daily run;
- source-health/record count retained by that run;
- origin/main persistence and post-run CI traceability.
