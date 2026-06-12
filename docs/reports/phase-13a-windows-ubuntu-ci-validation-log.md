# Phase 13A: Windows and Ubuntu CI Validation Log

## Public GitHub Actions Evidence

| Run | Commit | Ubuntu | Windows | Interpretation |
|---|---|---|---|---|
| `27336481022` | `47e6d0f9...` | pass | fail at tests | historical platform asymmetry |
| `27388260673` | `42c82f91...` | pass | pass | both platforms green before later incomplete release commits |
| `27391048701` | `308705e9...` | fail at tests | fail at tests | incomplete corrective commit |
| `27399295488` | `2ee4ee38...` | fail at tests | fail at tests | current origin/main lacks unstaged hotfix/doc corrections |

## Reproduction

A clean Git archive of `2ee4ee3` reproduced five failures:

1. README missing v0.4.1 release link;
2. stale v0.3.3 active-version test;
3. v0.4.1 release-doc README assertion;
4. Windows path separator failure;
5. doctor failure in the archive because `.git` was intentionally absent.

The first four explain failures in a real checkout. The fifth is an archive-only diagnostic artifact and is not evidence of the GitHub checkout state.

## Current Local Result

The working tree contains the path, release-doc, archival-version, doctor, and narrow submission-contract fixes. The repository helper completed with 471 passing tests. Release hygiene passed with the existing non-blocking legacy tracked-generated warning. These are local working-tree results only until the patch is published and CI reruns.

The public GitHub API was checked again on 2026-06-12. Run `27399295488` remains completed/failed, and both `Test (ubuntu-latest)` and `Test (windows-latest)` failed at `Run tests`. `gh` is installed but unauthenticated, so failed log text remains unavailable.
