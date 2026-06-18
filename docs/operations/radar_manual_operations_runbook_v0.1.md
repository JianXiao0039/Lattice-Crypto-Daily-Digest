# Radar Manual Operations Runbook v0.1

## Scope

This runbook is for manual operation of the public lattice/PQC paper radar by Codex, DeepSeek-Claude, or Kimi Code.

The radar product is Daily paper radar, Weekly synthesis, Monthly synthesis, source-health diagnostics, durable Markdown/JSON artifacts, reading queue, Obsidian note scaffolds, and recommendation rationales.

## Hard Boundaries

- Do not read or write `D:\Code\CodexProjects\PhD_Application`.
- Do not read or write `D:\ResearchArtifacts`.
- Do not write `D:\ResearchOS`.
- Do not create manual annotation or human-gold metric workflows.
- Do not create Task Scheduler jobs, cron jobs, startup tasks, watchers, background services, or automatic future runs.
- Do not run Git write operations unless a human explicitly starts a separate release/commit phase.
- Do not create, delete, move, or recreate release tags.
- Do not print secrets or `.env` contents.
- Do not use proxy rotation, fake User-Agent rotation, CAPTCHA bypass, hidden browser automation, or any source-access evasion.

## Path Setup

PowerShell:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
```

CMD:

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
```

Bash/MSYS/Git Bash:

```bash
cd /d/Code/CodexProjects/lattice-crypto-daily-digest
```

Do not mix CMD `cd /d` syntax with Bash paths.

## Required Pre-Run Checks

Run these before any Daily, Weekly, Monthly, full, backfill, source-health, durable-artifact, reading-queue, or Obsidian operation:

```powershell
Get-Location
git status -sb
python --version
python -m lattice_digest.workflow status
python -m lattice_digest.workflow doctor
```

If there are existing uncommitted changes, report them before generating new artifacts. Do not stage or commit generated artifacts in this runbook.

## Core Manual Commands

Daily latest 36h:

```powershell
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

Daily exact date:

```powershell
python -m lattice_digest.run --date YYYY-MM-DD --output markdown,json --send none
```

Weekly dry run and execution:

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
python -m lattice_digest.workflow weekly --low-load --skip-hygiene --execute
```

Monthly synthesis:

```powershell
python -m lattice_digest.monthly_synthesis --month YYYY-MM
```

Manual low-load source probe:

```powershell
python scripts\probe_source_health.py --low-load
```

Durable artifact verification:

```powershell
python scripts\verify_durable_artifacts.py --date YYYY-MM-DD --week YYYY-Www --month YYYY-MM
```

Reading queue and Obsidian export:

```powershell
python scripts\export_reading_queue.py --latest
python scripts\export_obsidian_notes.py --latest
```

## Output Review

For every generated Daily, Weekly, or Monthly Markdown file, check:

- It has paper-work rationale, not only keyword hits.
- Evidence basis is explicit.
- `TODO_VERIFY` is present where metadata, abstract, conclusion, parameters, benchmarks, or proofs are not fully available.
- It does not invent conclusion claims when no conclusion field exists.
- It distinguishes `精读`, `扫读`, `暂存`, and `忽略`.
- Source health affects reliability language honestly.
- Matching JSON is parseable and non-empty when records are expected.

## Bilingual Rationale Policy

For A-class, Must Read, top weekly, and top monthly papers, prefer compact bilingual rationale:

Chinese:

- 论文大致工作：
- 核心创新点：
- 与本雷达关系：
- 建议：
- TODO_VERIFY：

English:

- Paper work summary:
- Core novelty:
- Radar relevance:
- Recommendation:
- TODO_VERIFY:

Use compact Chinese-only rationale for peripheral B/C papers when output length would otherwise be excessive.

## Full Manual Run Definition

A full manual run is a foreground command sequence, not automation:

1. Pre-run checks.
2. Daily latest run or exact-date backfill.
3. Weekly dry run, then weekly execute if reasonable.
4. Monthly synthesis for the target month.
5. Source-health probe.
6. Durable artifact verification.
7. Reading queue export.
8. Obsidian export inside the repository.
9. Release hygiene check.
10. Final operation report.

No background service, scheduler, watcher, or automatic future run is part of the full manual run.

## Final Operation Report Template

- Operator:
- Date/time:
- Task:
- Commands run:
- Files generated:
- Files modified:
- Tests run:
- Source-health summary:
- Durable artifact status:
- Failures:
- `git status -sb`:
- Next recommended operator:
- Codex review required: yes/no
- Git write operations: forbidden unless separately confirmed by user
