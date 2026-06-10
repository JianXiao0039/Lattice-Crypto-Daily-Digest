# Phase 12U CI Triage Log

## Public GitHub Actions Evidence

Latest inspected CI run:

- run: `27291194097`;
- commit: `562dd01`;
- Windows job: success;
- Ubuntu job: failure;
- failed step: `Run tests`;
- release hygiene and diff hygiene: skipped on Ubuntu after the test failure.

The public check annotation only reported exit code 1. `gh` was not authenticated, so private job logs were not available through the CLI.

## Repository Workflow Audit

Command in `.github/workflows/ci.yml`:

```text
python -m pytest tests --basetemp=.pytest_tmp
```

The workflow is repository-scoped, uses Python 3.11, and installs `.[dev]` before tests.

## Linux Reproduction

Environment:

- WSL Ubuntu;
- isolated Python 3.11 runtime;
- package and test dependencies installed from the current project metadata;
- full Git clone, preserving `.git` for doctor/release-hygiene behavior.

Before fix:

```text
445 passed, 1 failed
```

Failure:

```text
test_reliability_baseline_contains_required_fields
expected: data\\2026-06-08.json
actual:   data/2026-06-08.json
```

An initial `git archive` reproduction also showed a doctor failure because the archive lacked `.git`. Repeating in a complete Git clone eliminated that artifact, proving it was not the GitHub CI failure.

## Fix Verification

- Windows focused tests: 4 passed.
- Linux/Python 3.11 focused tests: 4 passed.
- Linux/Python 3.11 full suite: 446 passed.
- Windows full suite: 446 passed.
- Linux/Python 3.11 full suite after the fix: 446 passed.
- Workflow doctor, CLI help, weekly handoff generation, release hygiene, and `git diff --check`: passed locally.

## Classification

Root cause: cross-platform path assertion in a test and OS-dependent artifact path serialization.

Not root causes:

- push failure;
- missing daily Markdown;
- bare pytest collection;
- unsupported CI Python;
- dependency installation;
- release hygiene;
- diff hygiene.
