# Phase 12Z: Version-Tag Consistency Resolution and First Post-Tag Run Review

## Executive Summary

The blocking hotfix is complete: reliability paths are portable, strict doctor is deterministic, and `Asia/Singapore` remains a real critical check. The doctor code 1 was not a timezone failure; staged `papers.db` caused the aggregate release-hygiene failure.

The immutable `v0.4.0` tag remains at `08c5f07967739ecd008773c4b167cd736848df88`, timestamp `2026-06-11T01:05:06+08:00`, with historical package metadata `0.3.3`. Resolution decision: `prepare_v0_4_1`. Active package sources are aligned to `0.4.1`; no tag is created.

The first post-tag Daily run is classified `non_persisted_automation_post_tag_actual`. It generated and verified the 2026-06-11 Markdown/JSON in an ephemeral runner, then failed in the commit step. The generated path families were ignored at the tag commit, conflicting with the workflow's explicit `git add`. No durable artifact reached Git or `origin/main`.

v0.5 offline precision design remains allowed. Production changes remain blocked.

## Blocking Hotfix

### Portable Paths

Root cause: Windows-native `str(Path)` serialization. The implementation now uses repository-relative `.as_posix()` for all reliability artifact fields and preserves missing values as `None`.

### Strict Doctor

The diagnostic report showed:

- Python: healthy;
- package version: healthy;
- `Asia/Singapore`: healthy and critical;
- release hygiene: failed because `papers.db` was staged.

Doctor now excludes staging policy from core health while explicit release hygiene still blocks forbidden staged generated files. Genuine critical failures remain nonzero.

## v0.4.0 Historical Evidence

| Field | Value |
|---|---|
| Tag | `v0.4.0` |
| Target | `08c5f07967739ecd008773c4b167cd736848df88` |
| Timestamp | `2026-06-11T01:05:06+08:00` |
| Historical package version | `0.3.3` |
| Tag action in Phase 12Z | none |

## Consistency Resolution

Decision: `prepare_v0_4_1`.

Active versions:

- `pyproject.toml`: `0.4.1`;
- source package: `0.4.1`;
- root bridge package: `0.4.1`.

Release notes and active tests are aligned. Historical v0.4.0/v0.3.3 facts remain documented.

## First Post-Tag Daily Run

| Field | Result |
|---|---|
| Run | `27327344162` |
| Automation | Daily Lattice Crypto Digest |
| Start/end | `2026-06-11T06:04:39Z` / `2026-06-11T06:07:00Z` |
| Target date | 2026-06-11 |
| Tests/generation/verification | success |
| Record count/source health | `TODO_VERIFY` |
| Commit | attempted, failed |
| Push | not reached with high confidence |
| Local/Git/origin persistence | no |
| Classification | `non_persisted_automation_post_tag_actual` |

The exact GitHub stderr is unavailable without authenticated log access. The path-policy conflict is independently verified and is the high-confidence failure cause.

## Windows and Ubuntu CI

- Ubuntu historical job: pass.
- Windows historical job: fail at tests.
- Confirmed Windows-specific failure class: `path_separator_related`.
- Local doctor failure class: `generated_file_related` / `dirty_worktree_related`, not timezone-related.
- Exact remote doctor assertion cause: `unresolved` until authenticated logs or a corrective CI rerun exist.

Local repository-scoped tests on Python 3.15.0b2 pass after the hotfix. The corrective patch has not been pushed, so no new CI claim is made.

## v0.5 Gate

- precision design: `design_ready_with_more_annotation`;
- production changes: `blocked_by_multiple_conditions`.

Remaining blockers include no durable Daily run, no actual post-tag Weekly run, pending Windows CI rerun, sample adjudication, and a separate Daily publication-path correction.

## Files Changed

The phase changes only:

- reliability/doctor/release-hygiene implementation needed for the hotfix;
- active version sources;
- focused tests;
- README, changelog, release notes, and Phase 12Z reports/policies.

No ranking, taxonomy, query, negative-keyword, source, classifier, or relevance semantics changed.

## Validation Results

- Python: `3.15.0b2`;
- imports and `ZoneInfo`: passed;
- reliability baseline tests: 2 passed;
- workflow command-center tests: 21 passed;
- release/version focused tests: passed;
- full repository tests: 464 passed;
- active package versions: all `0.4.1`;
- explicit release hygiene: blocked by pre-existing staged `papers.db`;
- `git diff --check`: passed;
- `v0.4.0`: unchanged at `08c5f07967739ecd008773c4b167cd736848df88`;
- worktree/index: dirty, with pre-existing staged generated/deletion changes plus unstaged Phase 12Z corrective files.

## TODO_VERIFY

- authenticated commit-step stderr for run `27327344162`;
- corrective Windows CI rerun;
- first durable post-tag Daily run;
- first actual post-tag Weekly run;
- separately approved workflow publication fix;
- clean release index before v0.4.1 tagging.
