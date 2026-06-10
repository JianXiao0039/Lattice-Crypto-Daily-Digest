# Full Manual Quality Run Stabilization Decision v0.1

Decision: `keep_paused`

## Reason

- Latest available daily artifact is degraded-but-usable.
- Tests and release hygiene pass.
- Full Manual Quality Run is still a heavy validation profile, not a daily/default automation.

## Run Once Manually If

- User decides to submit to GitHub.
- Missing dates are backfilled and need validation.
- Daily automation returns to repeated source-starved state.
- IACR latest repeatedly reports `failed/0`.
