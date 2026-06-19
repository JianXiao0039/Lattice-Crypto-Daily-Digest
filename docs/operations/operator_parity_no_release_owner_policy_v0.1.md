# Operator Parity No-Release-Owner Policy v0.1

Status: `operator_parity_no_release_owner_policy_ready`.

Codex remains the primary engineering and release-maintenance operator.

DeepSeek-Claude and Kimi Code are emergency manual fallback runners and reviewers. They must not become release owners.

Forbidden for DeepSeek-Claude and Kimi Code:

- release ownership;
- tag creation, deletion, movement, or recreation;
- git add, git commit, git push, or git tag;
- release-gate final decisions;
- broad source-health implementation changes;
- source fetcher changes;
- ranking, taxonomy, query expansion, or negative keyword changes;
- private path access;
- background automation.

Codex review is required before any DeepSeek-Claude or Kimi Code code, test, verifier, source-health, runbook, or release-gate change is treated as production-ready.
