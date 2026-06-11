# Phase 12V: v0.4 Tag Execution and Post-Tag Automation Observation

## Executive Summary

Phase 12V did not create, move, delete, or push a tag. A pre-existing remote lightweight tag named `v0.4.0` was discovered at commit `08c5f07967739ecd008773c4b167cd736848df88`.

The tag does not satisfy the Phase 12V release gates:

- GitHub Actions run `27292480658` failed on Windows;
- Phase 12U still records `tag_blocked_by_ci`;
- package and release metadata still declare `0.3.3`;
- the cross-platform implementation fix is present only as an unstaged local modification;
- the existing `v0.4.0` tag is lightweight, not the required annotated tag.

The daily digest files from 2026-06-04 through 2026-06-10 are present in `origin/main`, `--date` remains available, local tests pass with the unstaged fix, release hygiene passes for version `0.3.3`, and `git diff --check` passes. These results are not sufficient to validate the tagged commit.

## Pre-Tag Validation

| Gate | Result | Evidence |
|---|---|---|
| Remote daily digests through 2026-06-10 | pass | all seven Markdown files are in `origin/main` |
| `--date` CLI support | pass | visible in `python -m lattice_digest.run --help` |
| Local tests | conditional pass | 446 passed with an unstaged implementation fix |
| Release hygiene | pass for 0.3.3 | current package version is not 0.4.0 |
| `git diff --check` | pass | no whitespace errors |
| GitHub Actions | fail | Windows failed; Ubuntu passed for `08c5f07` |
| Phase 12U tag decision | fail | `tag_blocked_by_ci` |
| No private paths staged | pass | staging area is empty |
| No ResearchArtifacts staged | pass | staging area is empty |
| No staged secret files | pass | staging area is empty; no secret content was printed |

## Tag Execution Decision

Decision: **do not execute tag creation or tag push**.

The requested hard rule is not satisfied. The existing remote tag must not be silently rewritten. Remediation requires an explicit decision after CI and release metadata are corrected.

## Tag Execution Record

- tag name: `v0.4.0`
- discovered locally: yes
- discovered on origin: yes
- object type: lightweight tag pointing directly to a commit
- target commit: `08c5f07967739ecd008773c4b167cd736848df88`
- created by Phase 12V: no
- pushed by Phase 12V: no
- moved or deleted by Phase 12V: no
- release-valid: no

## GitHub Actions / CI Status

The current CI run for `08c5f07` is red:

- Ubuntu Python 3.11: success;
- Windows Python 3.11: failure.

The commit contains the POSIX-path test update but omits the matching implementation change in `src/lattice_digest/reliability_dashboard.py`. The missing implementation remains an unstaged local modification. This explains why local tests pass while the remote Windows job fails.

## Post-Tag Daily Monitoring Plan

Treat the existing tag as a premature release marker until remediated. After a valid release commit and green CI:

1. observe the next Daily Public Digest Run;
2. verify source-health counts and the source-starved guard;
3. verify IACR latest status and record count;
4. verify Semantic Scholar enrichment status without printing the key;
5. confirm daily Markdown and JSON artifact presence;
6. record the Actions result for the release commit or corrected release tag.

## Post-Tag Weekly Monitoring Plan

1. keep Weekly Public Synthesis active with the source-starved warning;
2. run the weekly handoff generator manually when validating a release;
3. confirm empty handoffs are explained rather than interpreted as no relevant papers;
4. verify track and non-claims fields remain present;
5. record candidate count and source-health caveats.

## Full Manual Quality Run Policy

Keep Full Manual Quality Run paused. Run it once manually only after the release commit is prepared or when a release regression appears. It must not become a background service.

## v0.4 to v0.5 Transition Plan

Before any v0.5 work:

1. resolve the incomplete v0.4 CI fix;
2. make version metadata, CHANGELOG, and release notes consistent;
3. obtain green CI for the exact release commit;
4. decide explicitly whether to preserve the existing `v0.4.0` tag and release a corrected `v0.4.1`, or remove and recreate `v0.4.0` only if rewriting the published tag is accepted;
5. freeze the corrected release before expanding reliability or research-track features.

## Known Risks

- The remote `v0.4.0` tag identifies a commit with failing Windows CI.
- The tag says v0.4.0 while package metadata says 0.3.3.
- The tag is lightweight rather than annotated.
- Local success currently depends on an unstaged source change.
- Rewriting a published tag can break downstream references and requires explicit approval.

## TODO_VERIFY

- commit and push the missing cross-platform implementation fix;
- prepare consistent 0.4.0 or 0.4.1 release metadata;
- obtain green Ubuntu and Windows CI;
- choose a safe policy for the already-published `v0.4.0` tag;
- observe the next Daily and Weekly automation runs after release correction.
