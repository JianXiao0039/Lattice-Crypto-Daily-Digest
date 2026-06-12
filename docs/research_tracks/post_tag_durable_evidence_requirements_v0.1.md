# Post-Tag Durable Evidence Requirements v0.1

A run is `durable_automation_post_tag_actual` only when all applicable evidence exists:

1. named automation run ID and post-tag start time;
2. generated Markdown and JSON paths;
3. source-health and record-count metadata;
4. successful validation;
5. successful commit or explicit artifact upload;
6. Git commit hash;
7. `origin/main` or authoritative artifact persistence;
8. IACR and Semantic Scholar state where available.

Generation inside an ephemeral runner without Git or artifact persistence is `non_persisted_automation_post_tag_actual`.
