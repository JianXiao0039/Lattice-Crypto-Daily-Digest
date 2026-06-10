# Weekly Synthesis Stabilization Decision v0.1

Decision: `keep_active_with_source_starved_warning`

## Reason

- Weekly handoff generation succeeds and produces 20 packets for `2026-W23`.
- Weekly artifact coverage is incomplete: expected 7 days, loaded 5, missing `2026-06-06` and `2026-06-07`.
- Weekly synthesis should remain active but must label source-starved and missing daily input.

## Required Behavior

- Run weekly handoff generator.
- Preserve non-claims policy.
- Do not interpret empty/missing input as no relevant papers.
- Do not write private application files.
