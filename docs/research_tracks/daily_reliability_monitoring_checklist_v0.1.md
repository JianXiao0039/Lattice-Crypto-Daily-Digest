# Daily Reliability Monitoring Checklist v0.1

Status: public monitoring checklist.

# After Each Daily Automation Run

- verify `python --version` policy still holds
- verify source health is present
- verify `source-starved` is explicitly labeled when applicable
- verify IACR latest status is present
- verify Semantic Scholar status is present without key leakage
- verify `git status -sb` is present
- verify no `PhD_Application` writes
- verify no `D:\ResearchArtifacts` writes

# After Each Weekly Automation Run

- verify weekly input file exists
- verify missing days are reported
- verify weekly handoff output exists or missing reason is explicit
- verify empty handoff is not overinterpreted

# Baseline Refresh Rule

- refresh baseline intentionally, not silently
- recommended cadence: weekly or after a meaningful recovery/state change
