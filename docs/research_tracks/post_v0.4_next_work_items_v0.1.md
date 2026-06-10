# Post-v0.4 Next Work Items v0.1

## Priority 1: CI

- obtain authenticated Ubuntu job logs;
- reproduce the failure on Linux/Python 3.11;
- add the narrowest cross-platform fix and regression test.

## Priority 2: Publication Policy

- decide whether official daily JSON is public;
- define how new ignored daily files enter an explicit publication commit;
- keep local test outputs excluded.

## Priority 3: Source-Starved Schema

- consider an additive `source_starved` and `empty_digest_reason` field;
- update Markdown wording and tests if approved.

## Priority 4: Weekly Refresh

- regenerate weekly synthesis from complete daily inputs;
- verify loaded/missing-day coverage;
- rerun weekly handoff.

## Priority 5: Observation

- observe the next Daily run;
- observe the next Weekly run;
- keep Full Manual Quality Run paused unless a trigger condition occurs.
