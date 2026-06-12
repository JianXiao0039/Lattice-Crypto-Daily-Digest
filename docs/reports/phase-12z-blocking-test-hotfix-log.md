# Phase 12Z: Blocking Test Hotfix Log

## Portable Path Failure

Root cause: reliability artifact paths had been serialized with `str(relative_path)`. Windows therefore emitted `data\2026-06-08.json` instead of the portable `data/2026-06-08.json`.

Fix:

- added private `_portable_relative_path()`;
- used `Path.relative_to(project_root).as_posix()`;
- covered daily JSON/Markdown, weekly JSON, and weekly handoff JSON;
- preserved `None` for missing artifacts;
- added explicit no-backslash regression assertions.

## Strict Doctor Failure

Diagnostic result:

- `Asia/Singapore timezone`: `ok=True`, `critical=True`;
- aggregate code 1 source: release hygiene rejected staged `papers.db`;
- Python prerelease, package version, directories, and timezone were healthy.

Fix:

- doctor checks release metadata and tracked-artifact health without consulting unrelated staging state;
- explicit `python scripts/check_release_hygiene.py` still enforces forbidden staged paths;
- a regression test confirms genuine critical hygiene failures still return code 1.

## Focused Validation

- reliability baseline tests: 2 passed;
- timezone doctor test: passed;
- workflow command-center tests: 21 passed;
- release/version documentation tests: 20 passed before the final release-doc expansion;
- full project tests after all edits: 464 passed.
