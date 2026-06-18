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
