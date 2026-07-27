# Weekly Digest Quality Policy v0.1

## Purpose

The weekly digest is a deterministic synthesis of canonical daily JSON artifacts. It does not retrieve fresh source data, mutate the reading queue, or change daily freshness and recommendation decisions.

## Weekly Safety Contract

- Weekly primary-new requires `primary_today_new_eligible=true` and `freshness_bucket=primary_today_new`.
- Recommendation score remains the freshness/risk-gated action score.
- Research value score represents intrinsic research value and cannot promote a stale item.
- Backfill remains non-primary even when its research value is high.
- TODO_VERIFY and hard source/date/venue risks route to verify-first and never read-now.
- Repeated daily appearances do not create fresh evidence.

## Deduplication And Provenance

Identity priority is DOI, arXiv identifier without a version suffix, IACR ePrint identifier, canonical source URL, then normalized title.

Duplicate merges preserve:

- all seen dates;
- all seen sources;
- source references and URLs;
- TODO_VERIFY flags;
- recommendation risk flags;
- per-occurrence placement context used by the Markdown audit appendix.

The private per-occurrence context is render-only and is removed before weekly JSON serialization. Weekly JSON remains schema version 1.

## Weekly Reading Decisions

The Markdown report separates:

- safe primary-new papers;
- high-value backfill and older papers;
- TODO_VERIFY and verify-first papers;
- user-aligned topic distribution;
- conservative venue and CCF counts;
- source-health confidence;
- read-only research-action queues.

Queue suggestions include read now, skim, save for background, verify first, Obsidian, blog, PhD/PI email, and project idea candidates. They do not write external state.

## Conservative Metadata Rules

- Only explicit CCF A/B/C values are counted as ranked venues.
- `N/A` remains a non-applicable source-type value, not a quality rank.
- Unknown venue or CCF metadata remains unknown or TODO_VERIFY.
- Crossref, DBLP, OpenAlex, and Semantic Scholar are metadata/indexing sources, not CCF authorities.
- Generated/translated markers and item-level TODO_VERIFY flags remain visible.

## Operational Boundaries

This weekly quality layer does not change:

- daily or weekly JSON schema;
- freshness policy;
- venue/CCF registry behavior;
- recommendation calibration logic;
- daily Markdown rendering;
- source retrieval behavior;
- canonical artifact overwrite policy;
- scheduling or automation.
