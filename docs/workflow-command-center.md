# Workflow Command Center

Phase 8J adds a small orchestration layer for the existing lattice digest research workflow. It does not replace the daily digest, weekly synthesis, reading queue, Obsidian scaffold, research artifact export, or research progress modules. It only coordinates them with safer defaults.

## 1. Safety Model

- No automatic scheduling is configured.
- All workflows are manually triggered by the user.
- The project does not install Windows Task Scheduler entries, cron jobs, startup tasks, background daemons, or background services.
- `daily`, `weekly`, and `full` default to dry-run.
- Use `--execute` only when you intentionally want files written.
- `status` and `doctor` never write files.
- Obsidian paper notes remain dry-run during `weekly --execute` unless `--generate-notes` is explicitly provided.
- Generated workflow manifests are written under `exports/workflow-runs/` and should not be committed.
- `--low-load` is recommended for laptops or manual runs where you want lower runtime and network pressure.

## 2. Common Commands

Plan a weekly workflow without writing files:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow weekly
```

Plan a low-load weekly workflow:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow weekly --low-load
```

Run the weekly workflow and write weekly outputs, artifact export, reading queue updates, and research progress logs:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow weekly --execute
```

Run the weekly workflow and also generate Obsidian paper note scaffolds:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow weekly --execute --generate-notes
```

Run the daily digest workflow:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow daily --execute --since 36h --output markdown,json --send none
```

Plan daily followed by weekly:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow full
```

Show local state without writing files:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow status
```

Run environment checks without writing files:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow doctor
```

## 2.1 Manual Low-Load Profiles

Supported profiles:

- `normal`: default manual dry-run profile.
- `low-load`: manually requested lower-load profile. Daily workflow uses a shorter default lookback when the workflow default `7d` has not been overridden.
- `offline/no-network`: skips network-dependent daily fetching and works only from existing local artifacts where possible.

Useful flags:

- `--low-load`
- `--offline`
- `--no-network`
- `--skip-heavy-sources`
- `--skip-zotero`
- `--skip-notes`
- `--skip-progress`

See [Manual Low-Load Workflow Profiles](manual-low-load-workflow.md).

## 3. Weekly Step Order

The weekly command uses a deterministic order:

1. Release hygiene check unless `--skip-hygiene` is used.
2. Weekly Research Synthesis.
3. Research Artifact Export Pack.
4. Reading Queue import.
5. Obsidian scaffold generation, dry-run unless `--generate-notes`.
6. Research Progress Log and Advisor Update.

This order lets the reading queue and progress log consume the latest weekly synthesis and artifact metadata.

## 4. Full Workflow

`full` runs the daily workflow first, then the weekly workflow. It preserves the same safety behavior: dry-run by default, writes only with `--execute`.

## 5. Manifest

When `weekly --execute` or `full --execute` succeeds, a manifest is written under:

```text
exports/workflow-runs/YYYY-MM-DD-weekly/manifest.json
exports/workflow-runs/YYYY-MM-DD-full/manifest.json
```

The manifest records:

- workflow name
- run date
- start and finish time
- dry-run flag
- step records
- outputs
- summary counts

## 6. Failure Behavior

The command center fails fast by default. If one step fails, the failing step is printed and the command returns a nonzero exit code. It does not hide partial failures.

## 7. What This Does Not Change

The workflow command center does not change:

- fetcher behavior
- ranking weights or thresholds
- daily digest section generation
- weekly synthesis aggregation
- source health semantics
- Zotero export behavior
- research artifact export behavior
- reading queue status semantics
- Obsidian note template semantics
- research progress semantics

## English Summary

The workflow command center is a deterministic CLI orchestrator for existing tools. It provides `daily`, `weekly`, `full`, `status`, and `doctor` commands. Writing workflows default to dry-run and require `--execute`; Obsidian note generation additionally requires `--generate-notes`. The module is intentionally thin and does not alter underlying ranking, digest, source health, Zotero, reading queue, artifact, or progress-log semantics.
