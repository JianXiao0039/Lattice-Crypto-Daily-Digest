# Phase 13G CI Confirmation Log

- Latest run: `27486931415`
- Workflow: CI
- Commit: `57a7b3af462d4436e320d1f029e88b41ccb0728a`
- Ubuntu: failure at `Run tests`
- Windows: failure at `Run tests`
- CI decision: `ci_red_both_platforms`
- `gh`: installed but unauthenticated
- Public API: run/job metadata available
- Failed test log: unavailable

A clean archive of the exact commit passed 521 tests locally under Python 3.15.0b2. CI uses Python 3.11, so the unresolved class is an environment difference affecting both platforms.
