# Full Manual Quality Run with Weekly Handoff v0.1

Status: public manual workflow guide.

# Purpose

Define a quality-first manual run sequence that can include weekly handoff generation as an explicit final step.

This is not an automatic workflow. The user runs each step manually.

# Manual Sequence

1. Check environment:

```powershell
python --version
python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"
```

2. Check workflow health:

```powershell
python -m lattice_digest.workflow doctor
```

3. Run or inspect the public digest / weekly synthesis manually according to the current task.

4. Generate weekly handoff packets only when needed:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\run_weekly_handoff.ps1
```

5. Review generated outputs:

```text
handoffs/weekly/YYYY-Www-handoff-packets.json
handoffs/weekly/YYYY-Www-handoff-packets.md
```

6. Run validation:

```powershell
scripts\run_project_tests.bat
python scripts\check_release_hygiene.py
git diff --check
git status -sb
```

# What This Adds

Weekly handoff generation becomes an explicit optional step in the full manual quality run.

# What This Does Not Add

- No scheduler.
- No background service.
- No startup task.
- No cron.
- No Windows Task Scheduler.
- No automatic ResearchArtifacts sync.
- No PhD application output.
- No change to daily/weekly workflow semantics.

# Non-Claims

Handoff packets are triage records only. They are not security proofs, novelty claims, construction-validity claims, PI-topic claims, or publication claims.

# TODO_VERIFY

- Whether weekly handoff outputs should be reviewed for several weeks before any code-level workflow integration.
- Whether handoff packet JSON should remain ignored by default.
- Whether ResearchArtifacts intake should stay manual.

