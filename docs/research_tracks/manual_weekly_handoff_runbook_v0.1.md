# Manual Weekly Handoff Runbook v0.1

Status: public manual-use runbook.

# Purpose

Generate weekly handoff packets from existing weekly JSON as a manual research radar step.

This runbook is for:

- Module-SIS chameleon hash related-work triage;
- public Xingye Lu bridge TODO_VERIFY candidates;
- AI4Lattice longline candidates;
- ML-KEM / ML-DSA background candidates;
- excluded generic/noise review.

It is not for PhD application material, private target PI email drafting, or automatic scheduling.

# Manual-Only Rule

No scheduled automation is configured. Do not create Windows Task Scheduler tasks, cron jobs, startup tasks, background services, watchers, or automatic future runs.

# Preconditions

- Weekly JSON exists under `data/weekly/`.
- Python environment imports `pytest`, `pydantic`, and `ZoneInfo("Asia/Singapore")`.
- `python -m lattice_digest.workflow doctor` passes.
- Work remains inside `D:\Code\CodexProjects\lattice-crypto-daily-digest`.

# Commands

cmd:

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
scripts\run_weekly_handoff.bat
```

PowerShell:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
powershell.exe -ExecutionPolicy Bypass -File scripts\run_weekly_handoff.ps1
```

Direct module command:

```powershell
python -m lattice_digest.weekly_handoff --latest
```

Dry-run:

```powershell
python -m lattice_digest.weekly_handoff --latest --dry-run
```

# Output

Default output:

```text
handoffs/weekly/YYYY-Www-handoff-packets.json
handoffs/weekly/YYYY-Www-handoff-packets.md
```

`handoffs/` is generated output and must not be committed by default.

# Review Checklist

- Confirm track counts and action counts.
- Review all `handoff_after_verify` records.
- Check lattice/PQC anchor evidence.
- Keep TODO_VERIFY and non-claims intact.
- Treat public Xingye bridge as tentative unless official evidence is verified.
- Exclude generic hash, commitment, AI, privacy, registration, blockchain, or ZK items without lattice/PQC anchor.
- Decide manually whether anything should be copied to ResearchArtifacts.

# Safety Boundaries

The helper does not:

- run `git add`, `git commit`, `git push`, or `git tag`;
- create scheduler entries;
- write into `PhD_Application`;
- write into ResearchArtifacts;
- fetch network sources;
- change ranking or taxonomy semantics.

