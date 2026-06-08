# Weekly Public Synthesis Run Prompt v0.3

Project path:

`D:\Code\CodexProjects\lattice-crypto-daily-digest`

Purpose:

Generate weekly public synthesis from current weekly artifacts, then generate weekly handoff, without overinterpreting sparse or source-starved inputs.

Weekly synthesis inputs:

- latest `data\weekly\*.json`
- latest `digests\weekly\*.md`
- latest `handoffs\weekly\*.json` if already present

Allowed commands:

- `python --version`
- `python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"`
- `python -m lattice_digest.workflow doctor`
- `python -m lattice_digest.workflow weekly --low-load --skip-hygiene`
- `scripts\run_weekly_handoff.bat`
- `python -m lattice_digest.weekly_handoff --latest`
- `git status -sb`

Forbidden commands and actions:

- no `git add`
- no `git commit`
- no `git push`
- no `git tag`
- no private folder writes
- no background automation

Weekly handoff guard:

- if `scripts\generate_weekly_handoff.py` is missing, do not claim it ran
- use `scripts\run_weekly_handoff.bat` or `python -m lattice_digest.weekly_handoff --latest`
- if handoff is empty, explain why
- if weekly input is source-starved or missing days, label coverage conservatively

Required reporting:

1. weekly input file used
2. missing days if any
3. handoff generation command actually used
4. packet count / excluded count / TODO_VERIFY count if available
5. source-starved weekly interpretation if applicable
6. final `git status -sb`
