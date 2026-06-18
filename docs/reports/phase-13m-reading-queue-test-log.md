# Phase 13M Reading Queue Test Log

## Focused Tests

Command:

```powershell
python -m pytest tests\test_reading_queue.py tests\test_obsidian_scaffold.py tests\test_obsidian_export.py tests\test_reading_queue_no_manual_annotation.py tests\test_reading_queue_rationale_integration.py -q --basetemp=.pytest_tmp
```

Result: `34 passed`.

## Manual Export Commands

```powershell
python scripts\export_reading_queue.py --latest
python scripts\export_obsidian_notes.py --latest
```

Results:

- Reading queue latest import: imported 0, updated 24, total 65, input `weekly_json`.
- Reading queue dashboard files written under `exports/reading-queue/`.
- Obsidian notes selected 33 records, refreshed 33 generated notes, skipped 0 manual notes.

## Notes

Generated Obsidian notes are UTF-8 without BOM, LF-only, deterministic, and have exactly one final newline in focused tests.
