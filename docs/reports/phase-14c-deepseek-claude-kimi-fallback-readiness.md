# Phase 14C DeepSeek-Claude / Kimi Fallback Readiness

Status: `fallback_ready_with_codex_review_required`.

DeepSeek-Claude may run manual workflows, inspect artifacts, summarize source health, review generated rationales, and draft low-risk docs.

Kimi Code may run safe manual commands, inspect generated artifacts, summarize outputs, and compare outputs against runbook expectations.

Both fallback operators must not:

- become release owners;
- run git add/commit/push/tag;
- create, delete, move, or recreate tags;
- read private paths;
- modify source fetchers, ranking, taxonomy, query expansion, or negative keywords;
- create background automation;
- use anti-bot bypass;
- claim unsupported command success.

Codex review is required for code, test, verifier, source-health, runbook, or release-gate changes.
