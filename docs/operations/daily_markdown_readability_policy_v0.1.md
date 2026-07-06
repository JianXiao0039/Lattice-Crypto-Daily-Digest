# Daily Markdown Readability Policy v0.1

## Purpose

The daily digest Markdown is the user-facing research triage surface. It must
make the reading decision clear before exposing detailed audit metadata.

## Invariants

- JSON schema is unchanged by the readability layout.
- Freshness policy is unchanged.
- Venue and CCF behavior is unchanged.
- Recommendation calibration logic is unchanged.
- Source retrieval behavior is unchanged.
- Backfill and TODO_VERIFY records must not look like primary today/new records.
- Generated and translated markers must remain visible.
- TODO_VERIFY and source-health risk must remain item-visible.

## Layout Contract

Daily Markdown should render:

1. title and run metadata;
2. `今日读什么 / What to read today` summary;
3. source-health and risk summary;
4. primary today/new section;
5. backfill / older / TODO_VERIFY section;
6. research actions and topic views;
7. source-health details;
8. detailed audit metadata.

## Per-Item Contract

Each item should show recommendation and action before deep audit fields:

- placement;
- source and selected date basis;
- venue and CCF;
- recommendation level, public recommendation score, and research value score;
- suggested action;
- why it matters;
- user relevance and PhD/application relevance;
- risk strip and TODO_VERIFY status;
- abstract/conclusion fields;
- audit details.

## Score Wording

`recommendation_score` is the freshness/risk-gated public action score.
`research_value_score` is intrinsic research value and must not promote stale or
backfill items into primary today/new.

## Low-Signal Days

No-primary or low-signal days must still answer what the user should do next:

- read now;
- skim;
- save for background;
- verify source first;
- skip today;
- expand to 7d or 30d only when useful.
