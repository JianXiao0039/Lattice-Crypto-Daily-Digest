# Automation UI Manual Update Checklist v0.1

# Current UI State

- Daily Public Digest Run: active
- Weekly Public Synthesis Run: active
- Full Manual Quality Run: paused

# Manual Update Steps

1. open the automation UI
2. find the existing `Daily Public Digest Run`
3. replace its prompt text with `docs/research_tracks/daily_public_digest_run_prompt_v0.3.md`
4. find the existing `Weekly Public Synthesis Run`
5. replace its prompt text with `docs/research_tracks/weekly_public_synthesis_run_prompt_v0.3.md`
6. find the existing `Full Manual Quality Run`
7. replace its prompt text with `docs/research_tracks/full_manual_quality_run_prompt_v0.3.md`
8. do not create duplicate modules unless the current ones are unusable
9. keep `Full Manual Quality Run` paused unless explicitly needed
10. do not enable any background service outside the ChatGPT automation UI

# Post-Update Validation

- next daily run produces a status report
- source-starved runs are labeled
- no private writes occur
- no git operations occur
- no secrets are printed
- next weekly run uses the actual working weekly handoff command
