# Phase 12U: GitHub Actions Failure Triage and Release Tag Decision

## Executive Summary

The GitHub push and daily Markdown submission are healthy: `2026-06-04` through `2026-06-10` are present locally, tracked by Git, and present in `origin/main`. The red X is a GitHub Actions test failure, not a push failure or missing-digest failure.

The latest CI run inspected was `27291194097` for commit `562dd01`. Its Windows Python 3.11 job passed; its Ubuntu Python 3.11 job failed during `Run tests`. The workflow already installs `.[dev]` and runs repository-scoped tests with `python -m pytest tests --basetemp=.pytest_tmp`.

A clean WSL Ubuntu/Python 3.11 clone reproduced the failure exactly: 445 tests passed and one test failed because `tests/test_reliability_baseline.py` expected Windows backslashes while Linux correctly returned POSIX separators. The implementation and test now normalize repository-relative artifact paths to POSIX form. After the fix, the complete Linux/Python 3.11 suite passes: 446 tests.

Tag decision: `tag_blocked_by_ci`. The fix has not yet been pushed and verified by GitHub Actions. In addition, release metadata still reports version `0.3.3`; a v0.4 tag must not be created until version metadata, CHANGELOG, and release documentation are explicitly updated.

## Remote Daily Digest Verification

- Local `HEAD` and `origin/main` were both `562dd01` at the start of the phase.
- `digests/2026-06-04.md` through `digests/2026-06-10.md` are present in the remote tree.
- Date-targeted `--date DATE` support remains visible in CLI help.
- Local JSON artifacts remain governed by the existing generated-artifact publication policy and are not the cause of the CI failure.

## Local Validation Results

### Before Fix

Clean Linux reproduction using WSL Ubuntu and Python 3.11:

- 445 passed;
- 1 failed;
- failure: `test_reliability_baseline_contains_required_fields`;
- expected `data\\2026-06-08.json` but Linux produced `data/2026-06-08.json`.

### After Fix

- Windows focused tests: 4 passed.
- Linux/Python 3.11 focused tests: 4 passed.
- Linux/Python 3.11 full suite: 446 passed.
- Final Windows project suite: 446 passed.
- Final Linux/Python 3.11 project suite: 446 passed.
- Release hygiene: passed; current declared version remains `0.3.3`.

## GitHub Actions Failure Classification

| Candidate cause | Classification | Evidence |
|---|---|---|
| Push/file submission failure | ruled out | remote daily Markdown files exist |
| Bare pytest collecting external packages | ruled out | workflow uses `python -m pytest tests --basetemp=.pytest_tmp` |
| Wrong CI Python version | ruled out | Python 3.11 is supported by the project and reproduces the issue correctly |
| Missing dependency installation | ruled out | workflow installs `-e ".[dev]"`; failure occurs after collection in one assertion |
| Missing generated files | ruled out for CI failure | reproduced failure uses a self-contained `tmp_path` fixture |
| Path mismatch | confirmed root cause | Windows-only separator assertion fails on Linux |
| Lint/diff/whitespace failure | ruled out | failure occurs in test step; later hygiene steps are skipped |
| Release-hygiene failure | ruled out for this red X | release hygiene was not reached on Ubuntu |
| Unknown CI-only issue | no longer primary | exact failure reproduced locally under Linux/Python 3.11 |

## Workflow Configuration Review

`.github/workflows/ci.yml` is unchanged.

The workflow correctly:

- uses Ubuntu and Windows matrices;
- uses Python 3.11;
- installs package and dev dependencies;
- runs repository-scoped tests;
- runs release hygiene and diff hygiene after tests.

No workflow weakening or operating-system exclusion is justified.

## Fixes Applied

### `src/lattice_digest/reliability_dashboard.py`

Repository-relative artifact paths now use `Path.as_posix()`. This creates stable JSON/report values across Windows and Linux.

### `tests/test_reliability_baseline.py`

Expected daily, weekly, and handoff artifact paths now use POSIX separators. The test verifies a cross-platform serialization contract instead of Windows behavior.

No source ingestion, ranking, taxonomy, source-health scoring, date-targeted generation, or workflow semantics changed.

## v0.4 Release Tag Decision

**Decision: `tag_blocked_by_ci`.**

Required before changing to `tag_ready`:

1. Commit and push the cross-platform path fix.
2. Confirm both Ubuntu and Windows CI jobs are green.
3. Update package version from `0.3.3` to the intended v0.4 version.
4. Add matching CHANGELOG and `docs/releases/` release notes.
5. Re-run release hygiene after the version update.
6. Obtain separate user approval before creating a tag.

## Manual Tag Checklist

- [ ] CI is green on Ubuntu and Windows for the exact release commit.
- [ ] `pyproject.toml` and `src/lattice_digest/__init__.py` expose the intended v0.4 version.
- [ ] CHANGELOG contains the same version and release date.
- [ ] `docs/releases/v0.4.0.md` or the selected exact version exists.
- [ ] Daily Markdown June 4-10 remains in `origin/main`.
- [ ] `--date` and source-starved regression tests pass.
- [ ] Release hygiene and `git diff --check` pass.
- [ ] Working tree contains no accidental generated/private artifacts in the release commit.
- [ ] User explicitly approves tag creation.
- [ ] Tag is created locally only after approval; tag push requires separate approval.

## Remaining Risks

- GitHub Actions has not yet evaluated the fix.
- Current package/release metadata remains `0.3.3`.
- Daily scheduled workflow failures are operationally separate and were not reclassified as the CI root cause.
- Existing generated-artifact ignore/publication policy remains unchanged.

## TODO_VERIFY

- next CI run for the cross-platform fix;
- exact v0.4 semantic version (`0.4.0` expected but not assumed);
- whether the next Daily scheduled run succeeds independently of CI;
- final release commit scope after metadata preparation.
