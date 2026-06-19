# Phase 14D Reading Queue / Obsidian Test Log

## Environment

- `python --version`: Python 3.15.0b2.
- `python -m lattice_digest.workflow doctor`: passed.
- `python -c "import lattice_digest; print(lattice_digest.__version__)"`: 0.4.1.

The local interpreter is Python 3.15.0b2, so this run verifies syntax and tests on the available local interpreter. The code changes avoid Python 3.12+ syntax and remain Python 3.11-compatible by construction.

## Compile Checks

- `python -m py_compile src/lattice_digest/reading_queue.py src/lattice_digest/obsidian_scaffold.py scripts/export_reading_queue.py scripts/export_obsidian_notes.py`: passed.
- Project has no `src/lattice_digest/obsidian_export.py`; Phase 14D used the actual implementation file `src/lattice_digest/obsidian_scaffold.py`.

## Focused Tests

`python -m pytest tests/test_reading_queue_direction_grouping.py tests/test_obsidian_deep_reading_scaffold.py tests/test_route_prompt_operator_safety.py tests/test_deepseek_kimi_fallback_policy.py tests/test_cross_operator_output_compatibility.py -q --basetemp=.pytest_tmp`

Result: 10 passed.

## Compatibility Tests

`python -m pytest tests/test_reading_queue.py tests/test_reading_queue_rationale_integration.py tests/test_reading_queue_no_manual_annotation.py tests/test_obsidian_scaffold.py tests/test_obsidian_export.py -q --basetemp=.pytest_tmp`

Result: 34 passed.

## Manual Export Checks

- `python scripts/export_reading_queue.py --latest`: passed; updated 24 existing queue records, total 65 records, wrote `state/reading-queue.json` and six repository-local reading queue dashboard files under `exports/reading-queue/`.
- `python scripts/export_obsidian_notes.py --latest`: passed; selected 33 notes and refreshed 33 repository-local paper notes under `exports/obsidian-paper-notes/Papers/`.

No export wrote to `D:\ResearchOS`.

## Full Validation

- `scripts/run_project_tests.bat`: passed, 680 tests.
- `python scripts/check_release_hygiene.py`: passed; reported version 0.4.1 and legacy tracked digest artifact notice.
- `git diff --check`: passed with CRLF normalization warnings on pre-existing modified/generated files.
- `git diff --cached --check`: passed.
- `git status -sb`: dirty worktree remains; no git staging, commit, push, or tag operation was executed.
