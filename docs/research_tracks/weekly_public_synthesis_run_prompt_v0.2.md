# Weekly Public Synthesis Run Prompt v0.2

Purpose:

Generate weekly public synthesis from current weekly artifacts, then run weekly handoff without overclaiming coverage.

Allowed commands:

- `python -m lattice_digest.workflow weekly --low-load --skip-hygiene`
- `scripts\run_weekly_handoff.bat`
- `python -m lattice_digest.weekly_handoff --latest`
- `python scripts\daily_reliability_dashboard.py`
- `git status -sb`

Quality gates:

1. weekly input exists
2. missing days are reported explicitly
3. weekly handoff generation succeeds or missing command is documented
4. empty handoff is explained
5. source-starved weekly input is labeled conservatively
6. handoff artifacts are present or missing reason is explicit
7. no private workspace is touched

Forbidden actions:

- no git add/commit/push/tag
- no private workspace writes
- no background scheduling

Notes:

- `scripts\generate_weekly_handoff.py` is currently not the supported repository entrypoint;
- use the `.bat` wrapper or `python -m lattice_digest.weekly_handoff --latest`.
