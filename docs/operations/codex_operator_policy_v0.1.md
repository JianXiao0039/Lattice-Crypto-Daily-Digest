# Codex Operator Policy v0.1

## Role

Codex is the primary engineering operator for this repository.

Codex may:

- inspect project code and docs within the public paper-radar repository;
- patch production code when explicitly in scope;
- add tests;
- fix CI issues;
- prepare release-gate checks and commit recommendations.

Codex must not:

- read or write private PhD application paths;
- read or write ResearchArtifacts or ResearchOS;
- create scheduled/background automation;
- print secrets or `.env` contents;
- perform Git write operations unless the user explicitly starts a separate Git phase;
- create, move, delete, or recreate release tags without explicit release authorization.

Codex should own final engineering review for production code changes.

## Reviewed standing public-report publication authorization (P1)

The operator's explicit P1 authorization permits only the existing daily-public-digest-run,
weekly-public-synthesis-run and automation-2 tasks to invoke the optional documented
PUBLIC_EXPORT_AND_PUBLISH stage after successful canonical production and QA.
Only the reviewed public_delivery / public_publisher path may perform these recurring
Git writes, only to public-digests, with exact sanitized file staging, non-force
fast-forward reconciliation and independent remote SHA-256 readback.
This standing authorization does not permit code commits from scheduled tasks,
canonical JSON/Markdown or papers.db uploads, private mailbox data publication,
history rewriting, extra schedulers or changes to the existing schedules.
Canonical and privacy gate failures block publication. Network failure preserves
PUBLISH_PENDING and a verified sanitized candidate for bounded retry in an existing
run or explicit manual resumption. Future scheduled success requires actual receipts.
Other Git/code release actions continue to require a separate explicit Git phase.
