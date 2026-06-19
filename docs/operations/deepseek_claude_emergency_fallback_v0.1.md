# DeepSeek-Claude Emergency Fallback v0.1

Status: `fallback_ready_with_codex_review_required`.

DeepSeek-Claude may be used when Codex is unavailable or the user only needs a low-risk manual radar run.

Allowed:

- run Daily, Weekly, Monthly, source-health probe, durable verification, reading queue export, Obsidian export, and monthly quality audit commands;
- inspect generated Markdown and JSON inside this repository;
- summarize source health and recommendation rationale quality;
- draft low-risk documentation notes.

Forbidden:

- acting as release owner;
- git add, git commit, git push, or git tag;
- tag creation, deletion, movement, or recreation;
- source fetcher changes;
- ranking score or threshold changes;
- taxonomy, query expansion, or negative keyword changes;
- private path access;
- background automation;
- anti-bot bypass or access-control evasion;
- unsupported command-success claims.

Codex review is required if DeepSeek-Claude changes code, tests, source-health classification logic, durable verification logic, operation runbooks, or release-gate documents.
