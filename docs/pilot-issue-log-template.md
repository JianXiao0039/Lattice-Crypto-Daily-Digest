# Pilot Issue Log Template

Use this template during the one-week manual pilot. Keep entries factual and reproducible. Do not include API keys, SMTP passwords, Zotero tokens, or private notes.

English summary: this template is for manual pilot issues only. No scheduled automation is configured, and generated artifacts must not be committed.

## Issue categories

Choose one or more:

- false positive classification
- missing important paper
- noisy ranking explanation
- confusing workflow output
- slow command
- generated artifact clutter
- reading queue status problem
- Obsidian scaffold problem
- source health confusion
- Windows path issue
- SQLite file lock issue
- CI-only issue
- documentation gap

## Entry template

### Issue title

- Date:
- Command run:
- Expected behavior:
- Actual behavior:
- Severity: low / medium / high
- Reproduction steps:
- Suspected cause:
- Proposed fix:
- Phase target:
- Status: open / triaged / fixed / won't fix

## Example entry

### Weekly low-load dry-run output was confusing

- Date: 2026-06-01
- Command run: `python -m lattice_digest.workflow weekly --low-load --skip-hygiene`
- Expected behavior: dry-run default prints planned steps and writes no files.
- Actual behavior: TODO_FILL_IN.
- Severity: low / medium / high
- Reproduction steps:
  1. Run the command manually in PowerShell.
  2. Capture the exact output.
  3. Check `git status -sb`.
- Suspected cause: TODO_VERIFY.
- Proposed fix: TODO_VERIFY.
- Phase target: Phase 9D or later maintenance phase.
- Status: open / triaged / fixed / won't fix

## Pilot-specific reminders

- manual-only usage remains the rule.
- dry-run default should be checked before any `--execute` run.
- low-load mode should be preferred on laptops.
- no-network or offline usage should be used when avoiding external fetches.
- reading queue manual statuses should be preserved.
- generated artifacts must not be committed.
