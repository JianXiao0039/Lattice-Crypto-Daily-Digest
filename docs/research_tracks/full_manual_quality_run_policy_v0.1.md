# Full Manual Quality Run Policy v0.1

Status: public full-manual-module policy.

# Role

The Full Manual Quality Run is a heavier validation path. It is appropriate for:

- complete workflow validation;
- source recovery pilot;
- tests;
- release hygiene;
- weekly handoff re-run;
- repository health checks.

# Why It Can Remain Paused

It is intentionally heavier than daily/weekly paths and should not behave like a default automation loop.

# Must Not Do

- create background jobs;
- auto-commit;
- auto-push;
- write private application material;
- mutate business logic unless explicitly requested.

# Recommended Use

Use it when source health is degraded, when several daily runs look source-starved, or when a full validation pass is required before trusting public radar outputs.

