# Cross-Operator Manual Workflow Parity v0.1

Status: `codex_deepseek_kimi_parity_ready`.

This document standardizes the public paper-radar manual workflow for Codex, DeepSeek-Claude, and Kimi Code.

All operators must work only inside:

`D:\Code\CodexProjects\lattice-crypto-daily-digest`

All operators must avoid:

- `D:\Code\CodexProjects\PhD_Application`;
- `D:\ResearchArtifacts`;
- `D:\ResearchOS`;
- secrets and `.env` contents;
- manual annotation or human-gold workflows;
- release tag creation, deletion, movement, or recreation;
- git add/commit/push/tag operations;
- Task Scheduler, cron, watchers, startup tasks, background services, or automatic future runs;
- proxy rotation, fake User-Agent rotation, CAPTCHA bypass, hidden browser automation, SSL verification disablement as a production default, or access-control evasion.

## Shared Pre-Run Checks

PowerShell:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
git status -sb
python --version
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
```

If `workflow status` is unavailable, report it as unavailable, run `doctor`, and continue only if `doctor` passes.

## Role Parity

Codex is the primary engineering and release-maintenance operator.

DeepSeek-Claude is a backup manual runner and reviewer.

Kimi Code is a lightweight emergency fallback runner.

DeepSeek-Claude and Kimi Code may run documented manual commands and inspect generated artifacts. They are not release owners and must not commit, push, or tag. Any code or test change requires Codex review.

## Shared Final Report

Every operator must write the same operation report structure from `docs/operations/manual_operator_report_template_v0.1.md`.
