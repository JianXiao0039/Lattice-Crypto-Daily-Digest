# Weekly Automation Resume Decision v0.1

## Decision

`keep_active_with_source_starved_warning`

## Rationale

- Weekly synthesis and handoff generation remain operational.
- The current W23 artifact was generated before recovered June 6 and June 7 inputs were available.
- The handoff contains 20 packets but inherits stale W23 coverage.
- Empty or incomplete weekly results must not be interpreted as no useful papers.

## Required Next Run

- Rebuild weekly synthesis from complete daily inputs.
- Confirm loaded and missing day lists.
- Regenerate handoff from the refreshed weekly JSON.
- Record source-starved and source-health caveats.

