# Weekly Handoff Migration Plan v0.1

Status: public migration plan. No code is changed in Phase 12F.

# Goal

Move from documentation-only track synthesis to stable manual weekly handoff packets without changing existing weekly semantics.

# Phase 1: Template-Only

Current state:

- track definitions exist;
- weekly template exists;
- related-work radar exists;
- bridge map exists;
- packet template and non-claims policy exist.

Action:

- continue manual review;
- validate track boundaries;
- keep all candidate claims TODO_VERIFY.

Exit criteria:

- users can produce a valid packet manually;
- packet schema and decision rubric are accepted.

# Phase 2: Manual Handoff Packets

Action:

- manually create reviewed packets from weekly JSON and public reports;
- store drafts in an ignored public output directory or local ResearchArtifacts radar folder;
- record accepted/rejected intake manually.

Exit criteria:

- several weeks of packet examples;
- stable field needs;
- false-positive patterns documented.

# Phase 3: Generated Handoff JSON/Markdown

Action:

- add standalone `weekly_handoff` module;
- read existing weekly JSON only;
- default to dry-run;
- generate packets and exclusions deterministically;
- preserve existing weekly outputs.

Exit criteria:

- fixture tests pass;
- ranking and weekly outputs unchanged;
- no private or cross-workspace write by default.

# Phase 4: Optional ResearchArtifacts Sync

Action:

- add explicit manual mirror option;
- require a supplied target directory;
- reject private paths;
- write packet/summary files only;
- do not update artifact code or paper claims automatically.

Exit criteria:

- boundary tests pass;
- artifact intake workflow is reviewed;
- non-claims remain intact.

# Phase 5: Stable Weekly Handoff

Action:

- optionally expose the standalone generator through the manual workflow command center;
- keep dry-run default;
- require explicit execute and explicit mirror;
- document generated artifacts as uncommitted by default.

Exit criteria:

- multi-week pilot demonstrates deterministic, useful packets;
- noise rate is acceptable;
- no ranking/source/workflow regressions;
- no scheduled automation.

# Backward Compatibility

- Keep existing weekly JSON/Markdown schema and rendering unchanged.
- Handoff receives a separate schema and output directory.
- Do not repurpose `idea_bank_candidates` or `paper_plan_candidates`.
- Do not change relevance scores, labels, thresholds, taxonomy, or source health.

# Rollback Plan

Because handoff is a separate module/output:

- disable or stop calling the handoff generator;
- remove generated packet outputs;
- leave weekly synthesis untouched;
- preserve manual protocol documents.

# Open Decisions

- standalone CLI only versus later workflow integration;
- one weekly packet file versus per-packet files;
- whether public generated packets remain ignored;
- whether ResearchArtifacts mirror is summary-only or packet-level;
- whether `handoff_now` always requires original-paper reading.

# Non-Goals

- no fetching;
- no automatic source retry;
- no ranking changes;
- no automated proof or construction claims;
- no automatic ResearchArtifacts code modification;
- no private application material;
- no scheduler or background execution.

