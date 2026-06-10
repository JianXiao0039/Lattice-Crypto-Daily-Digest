# Weekly Automation Monitoring Loop v0.1

## Purpose

Keep Weekly Public Synthesis active while preventing stale or source-starved daily inputs from being overinterpreted.

## After Each Run

1. Confirm weekly Markdown and JSON exist.
2. Inspect expected, loaded, and missing dates.
3. Aggregate source-health caveats across loaded days.
4. Mark incomplete/source-starved coverage explicitly.
5. Run the weekly handoff generator.
6. Record packet, excluded, and TODO_VERIFY counts.
7. Explain empty handoff output instead of treating it as no relevant candidates.
8. Confirm the report remains track-based and does not create private application material.

## Keep Active When

- weekly inputs are identifiable;
- missing-day and source-starved warnings are visible;
- handoff output is generated or its absence is explained.

## Manual Intervention When

- weekly coverage is stale after daily backfill;
- several daily inputs are source-starved;
- handoff packets are based on missing daily dates;
- source-health summaries disagree with daily artifacts.

## Non-Automation Boundary

Do not auto-sync to ResearchArtifacts, auto-commit, auto-push, or create background recovery jobs.
