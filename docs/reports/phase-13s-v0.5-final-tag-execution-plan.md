# Phase 13S v0.5 Final Tag Execution Plan

## Decision

`tag_plan_blocked`

No tag was created, moved, deleted, or pushed in this phase.

## Phase 13CI Import Fix Summary

GitHub Actions failed on Python 3.11 during collection because dynamic imports loaded `scripts/evaluate_v0_5_track_precision.py` without registering the module in `sys.modules` before `spec.loader.exec_module(module)`.

That file defines `@dataclass(frozen=True)` classes. Python 3.11 dataclasses inspect `sys.modules[cls.__module__]` while processing the decorator, so an unregistered dynamic module can raise:

`AttributeError: 'NoneType' object has no attribute '__dict__'`

The local compatibility fix registers dynamic modules in `sys.modules` before `exec_module`, and removes the registration on import failure.

Changed files:

- `scripts/run_v0_5_shadow_pilot.py`
- `tests/test_v0_5_shadow_pilot.py`
- `tests/test_v0_5_track_precision_evaluation.py`
- `tests/test_python311_dynamic_import_compatibility.py`

Focused validation:

- `python -m py_compile scripts/evaluate_v0_5_track_precision.py`: passed.
- `python -m py_compile scripts/run_v0_5_shadow_pilot.py`: passed.
- `python -m pytest tests/test_v0_5_track_precision_evaluation.py tests/test_v0_5_shadow_pilot.py tests/test_python311_dynamic_import_compatibility.py -q --basetemp=.pytest_tmp`: 14 passed.

## Dependency Status

Phase 13Q final release decision exists and records v0.5 as blocked by multiple conditions.

Phase 13R monthly real-case audit exists and records:

- monthly rationale quality: `monthly_rationale_quality_passed_with_limits`;
- real paper audit: `real_case_audit_completed`;
- keyword-only regression: passed;
- bilingual status: `bilingual_policy_documented_but_not_rendered`;
- reading decision usefulness: `reading_decision_useful_with_limits`.

Phase 13P release-gate cleanup exists and records:

- v0.4.1 as an existing blocked historical tag;
- v0.5 RC as ready with limits;
- durable evidence ready for representative v0.5 artifacts;
- CI unavailable from local environment at that phase;
- release notes needing cleanup.

Operations runbook exists:

- `docs/operations/radar_manual_operations_runbook_v0.1.md`

## Gate Review

| Gate | Status | Evidence |
| --- | --- | --- |
| CI import issue fixed locally | pass | Focused Python import tests pass locally |
| Remote CI green | blocked | Needs commit/push by user-confirmed phase and GitHub Actions verification |
| Durable evidence | pass | Phase 13P/13Q recorded representative Daily/Weekly/Monthly verification |
| Source health | pass with explicit degradation | Phase 13Q records source-health acceptable with explicit degraded states |
| Monthly real-case rationale audit | pass with limits | Phase 13R scorecard average 4.38, keyword-only regression passed |
| Operations runbook | pass | Phase 13O runbook exists |
| Release notes clean | blocked | Phase 13Q records release notes need cleanup |
| No manual annotation dependency | pass | Existing final gate docs record no dependency |
| No background automation | pass | Operations runbook forbids automation |

## Tag Readiness

`tag_plan_blocked`

The v0.5 tag must not be created yet because remote CI is not verified green after the Python 3.11 import fix, and release notes are still recorded as needing cleanup.

## Required Next Actions

1. Commit the Python 3.11 dynamic import compatibility fix in a separate user-confirmed Git phase.
2. Push the commit and verify GitHub Actions on Ubuntu and Windows.
3. Clean v0.5 release notes so they do not overstate final release status, CI status, source-health recovery, or v0.4.1 validity.
4. Re-run the v0.5 final gate checks.
5. Only after all gates pass, enter a separate user-confirmed tag execution phase.

## Conditional Tag Command Status

Tag commands are not ready for execution in Phase 13S.

If a later phase verifies CI green and release notes clean, the semver-consistent tag name should be `v0.5.0`, because existing release tags use `v0.1.0`, `v0.2.0`, `v0.2.1`, `v0.3.0`, `v0.3.1`, `v0.3.2`, `v0.3.3`, `v0.4.0`, and `v0.4.1`.

## Boundaries

- No `git add`, `git commit`, `git push`, or `git tag` was executed.
- No tag was created, deleted, moved, or recreated.
- No private project, ResearchArtifacts, or ResearchOS path was read or written.
- No manual annotation workflow was introduced.
- The production paper-radar pipeline remains centered on Daily, Weekly, and Monthly paper discovery.
