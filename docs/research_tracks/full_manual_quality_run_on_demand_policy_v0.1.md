# Full Manual Quality Run On-Demand Policy v0.1

## State

Keep the module paused.

## Run Manually When

- preparing a release candidate;
- CI and local results disagree;
- all-red source health persists;
- weekly synthesis must be rebuilt after backfill;
- release hygiene or repository boundaries require a full audit.

## Required Checks

- environment imports and doctor;
- source connectivity when relevant;
- complete project tests;
- release hygiene;
- weekly handoff regeneration;
- Git diff and status review;
- private-boundary confirmation.

## Forbidden Behavior

- no scheduler or background service;
- no automatic tag;
- no private workspace writes;
- no secret output;
- no unreviewed business-logic mutation.
