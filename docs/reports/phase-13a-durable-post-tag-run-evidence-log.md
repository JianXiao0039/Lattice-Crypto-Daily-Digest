# Phase 13A: Durable Post-Tag Run Evidence Log

## Observation Table

| Run | Date | Class | Generation | Retained files | Git/origin | CI | Verdict |
|---|---|---|---|---|---|---|---|
| `27327344162` | 2026-06-11 | `non_persisted_automation_post_tag_actual` | tests, generation, and validation passed | none retained | commit failed; no push/origin files | workflow failed | real run, not durable |
| `27397762239` | 2026-06-12 | `non_persisted_automation_post_tag_actual` | tests failed; generation skipped | none | no commit/push | workflow failed | real run, not durable |

Durable automation runs: 0.

## Run 27327344162

- Automation: `Daily Lattice Crypto Digest`
- Event: schedule
- Start: `2026-06-11T06:04:39Z`
- Job end: `2026-06-11T06:07:00Z`
- Head: `08c5f07967739ecd008773c4b167cd736848df88`
- Target date: 2026-06-11
- Artifact verification: passed in runner
- Record count/source health: `TODO_VERIFY`
- Commit: failed
- Push: not reached with high confidence
- `origin/main`: no 2026-06-11 Markdown or JSON
- Failure class: generated-artifact allowlist/staging contract

## Run 27397762239

- Automation: `Daily Lattice Crypto Digest`
- Event: schedule
- Start: `2026-06-12T06:00:37Z`
- Head: `308705e9...`
- Target date: 2026-06-12
- Tests: failed
- Generation, verification, commit, and email: skipped
- `origin/main`: no 2026-06-12 Markdown or JSON
- Failure class: repository test failure before generation

## Current Evidence Gap

The narrow submission contract is locally implemented and tested but is not yet published. No run has exercised it, so no durable classification is available.
