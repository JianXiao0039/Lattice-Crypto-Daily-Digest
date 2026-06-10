# Full Manual Quality Run Pause Decision v0.1

## Decision

`keep_paused`

## Rationale

- Full local validation is being performed manually in Phase 12S.
- A continuously active heavy module is unnecessary.
- The unresolved CI issue is Ubuntu-specific and should be diagnosed from Actions logs or a Linux reproduction, not by creating background automation.

## Manual Use Conditions

Run once manually when:

- source health remains all red across repeated runs;
- weekly synthesis must be rebuilt after backfill;
- a release candidate needs complete tests and hygiene checks;
- CI failure needs a controlled local reproduction.

Do not use it as a scheduler, background service, auto-commit path, or private-workspace writer.

