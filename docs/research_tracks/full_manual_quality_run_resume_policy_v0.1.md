# Full Manual Quality Run Resume Policy v0.1

Status: keep paused.

## Resume Temporarily Only When

- Two consecutive latest daily runs are source-starved.
- IACR latest repeatedly reports `failed/0`.
- Semantic Scholar repeatedly fails with auth, rate-limit, or network failure and needs manual diagnosis.
- A release or broad repository health check is needed.
- The user explicitly asks for a full manual quality run.

## Do Not Use It For

- Routine daily digest generation.
- Background retry.
- Scheduled source recovery.
- Automatic git operations.
- Private PhD application material.
- ResearchArtifacts writes.

## Manual-Only Rule

Full Manual Quality Run is a heavy validation profile, not a background service.
