# Phase 14B Bilingual Rationale Test Log

## Focused Tests

Command:

`python -m pytest tests/test_bilingual_rationale_polish.py tests/test_bilingual_terminology_stability.py tests/test_bilingual_rationale_no_overclaim.py tests/test_top_paper_bilingual_rendering.py -q --basetemp=.pytest_tmp`

Result:

`9 passed`

## Py Compile

Command:

`python -m py_compile src/lattice_digest/recommendation_rationale.py`

Result:

passed.

## Monthly Audit

Command:

`python scripts/audit_monthly_rationale_quality.py --latest`

Result:

- decision: `monthly_rationale_quality_passed_with_limits`;
- quality score: 83;
- bilingual rationale: `bilingual_top_paper_rationale_present`.

Full validation status is recorded in the final Phase 14B response.

## Full Project Tests

Command:

`scripts/run_project_tests.bat`

Result:

`656 passed in 31.78s`

## Release Hygiene

Command:

`python scripts/check_release_hygiene.py`

Result:

passed.

Notes:

- active version: `0.4.1`;
- legacy tracked digest artifacts are still present, but hygiene passes in the current non-strict mode.

## Diff Checks

Commands:

- `git diff --check`
- `git diff --cached --check`

Result:

- `git diff --check`: passed with CRLF-to-LF warnings for existing modified/generated files;
- `git diff --cached --check`: passed.
