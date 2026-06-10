# Daily Automation Resume Decision v0.1

## Decision

`keep_active_but_monitor`

## Rationale

- Daily generation and date-targeted recovery work locally.
- June 4-10 Markdown is now remote.
- Local and Windows CI validation pass.
- Ubuntu CI remains red.
- New daily paths still match ignore rules, so publication must be verified separately from generation.
- Source-starved artifacts are preserved, but explicit classification is incomplete.

## Required Monitoring

1. Verify Markdown and JSON existence after each run.
2. Record source green/yellow/red counts.
3. Treat zero records plus all-red sources as source-starved.
4. Verify whether each new date is Git-tracked when publication is intended.
5. Do not report success when generation succeeded but publication did not.
6. Do not print API keys or create background retry loops.

