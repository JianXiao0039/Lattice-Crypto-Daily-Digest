# Weekly Prompt v0.3 Adjustment Recommendations v0.1

Recommendation: keep v0.3 unchanged.

## Required Behavior to Preserve

- Run weekly handoff generation manually.
- Label source-starved weekly input.
- Do not overinterpret empty handoff output.
- Keep handoff packets as research triage records only.
- Do not write private application material.

## Current Check

- `python scripts\generate_weekly_handoff.py --latest` ran successfully.
- Latest handoff: `handoffs\weekly\2026-W23-handoff-packets.json`
- Packet count: `20`
