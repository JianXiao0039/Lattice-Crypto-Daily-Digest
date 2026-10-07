# Public runtime isolation and exact recovery

Public code runs from a published, clean checkout. Set one absolute artifact root:

```powershell
Set-Location 'D:\Code\CodexProjects\lattice-crypto-daily-digest-runtime'
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
$env:LATTICE_DIGEST_CANONICAL_ROOT = 'D:\Code\CodexProjects\lattice-crypto-daily-digest'
& 'D:\CyberSecurity\Python315\python.exe' -m lattice_digest.public_daily --preflight --since 36h
& 'D:\CyberSecurity\Python315\python.exe' -m lattice_digest.public_weekly --preflight
& 'D:\CyberSecurity\Python315\python.exe' -m lattice_digest.public_monthly --preflight
```

`RuntimePaths` anchors imports/config to code and derives data, digests, audits,
state, exports and papers.db from the canonical root. No artifacts are copied or
moved. Public entries require the explicit canonical root and code CWD. A
canonical development checkout must not occur on Python's import path.
Without the root environment variable the existing manual CLIs retain their
defaults. Public entries are fail-closed regardless of `--dry-run`/`--preflight`.

Public Daily retains the strict workflow doctor. Weekly uses the preceding
Monday-Sunday period by default. Monthly defaults to the preceding calendar
month. Explicit period arguments remain available. Monthly `--exports` enables
queue, artifact and progress operations; `--exports --obsidian` additionally
enables create-only published notes. Existing notes are preserved. The old
export script's unsupported refresh argument is removed; no dirty renderer or
writing changes are integrated. All downstream paths derive from RuntimePaths.
Optional profiles must match the operations actually enabled in the saved prompt.

Public secret configuration uses existing process variables or an explicitly
named absolute `LATTICE_DIGEST_ENV_FILE`. Process variables take precedence.
Public code never implicitly reads a development `.env`. Manual Daily retains
code-root `.env` compatibility. Preflight does not load secret values. The
Semantic Scholar key and OpenAlex contact email are optional for the published
adapters; OPENAI_API_KEY is carried in context but no source adapter consumes it.

## Provenance and manifest maintenance

`config/runtime_dependencies.json` contains DAILY, WEEKLY, MONTHLY,
MONTHLY_EXPORTS and MONTHLY_OBSIDIAN. Authority comes from the published Git
blob. A working-tree edit to the manifest cannot exclude a dependency.
Content hashes normalize CRLF like Git text checkouts; staged changes also block.
Missing files and paths that resolve outside the checkout block.

| State | Public behavior |
| --- | --- |
| PUBLISHED_CLEAN_RUNTIME | Allowed |
| PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_WORKTREE | Allowed; command dependencies must still match |
| DIRTY_RUNTIME_DEPENDENCY | Block |
| UNPUBLISHED_RUNTIME_COMMIT | Block for any unequal HEAD, including documentation-only commits |
| UNKNOWN_RUNTIME_PROVENANCE | Block |

Public entries read live remote main before executing. Metadata explicitly
distinguishes live authority from cached local refs used by read-only audits.
No bypass flag or environment variable exists. Scheduler metadata stays UNKNOWN
unless supplied explicitly. Executing period workflows write real finish
telemetry under canonical audits/runtime; preflight writes nothing.

The checker computes static local imports, including function-local imports,
and compares exact manifest membership. Workflow doctor is analyzed through its
reviewed callable scope, including top-level imports and its helper calls.
Monthly boolean branches are pinned to each public profile. Unknown dynamic
execution and unresolved local imports fail closed. Public preflight imports
the entire reviewed closure and rejects observed repository imports outside it
or outside code_root. This does not claim a perfect analyzer for arbitrary
Python metaprogramming. New dynamic loading requires explicit review.

```powershell
python -m scripts.check_runtime_dependencies
# Only after reviewing changed import/config/non-Python dependencies:
python -m scripts.check_runtime_dependencies --write
```

The Daily doctor reads release-version metadata in CHANGELOG.md and requires the
version-specific release document to exist. Those two files are included for
that executed preflight; other documentation and generated artifacts are absent.
Dependency declarations/available lockfiles are reviewed non-Python inputs.

Dirty weekly_handoff.py and run_local_digest_backfill.ps1 do not affect ordinary
public Daily. workflow.py affects Daily through doctor. obsidian_scaffold.py
affects only MONTHLY_OBSIDIAN. No dirty development file is promoted by this rule.

## Exact historical recovery interface

The following invocation is preparation only and performs no discovery or writes:

```powershell
& 'D:\CyberSecurity\Python315\python.exe' -m lattice_digest.public_daily `
  --preflight --run-mode backfill --target-date 2026-10-07 --since 36h `
  --coverage-start '2026-10-05T21:04:26.631541+08:00' `
  --coverage-end '2026-10-07T09:04:26.631541+08:00' `
  --original-missing-reason PUBLIC_AUTOMATION_RUNTIME_CODE_BLOCKED
```

Both offsets and endpoints are preserved. The CLI rejects missing endpoints,
naive times, reversed/empty windows, absent target dates, non-backfill mode and
a supplied --since inconsistent with duration. Without --since the exact
duration is recorded. Normal Daily ends at its actual Asia/Singapore start
timestamp and looks back 36 hours; calendar --date remains 24 hours.

Recovery metadata separates target/window, actual execution and original missing
reason. In preflight, recovery execution timestamps remain UNKNOWN. Actual
recovery uses BACKFILL and preserves requested endpoints. Exact publication
materializes and validates a disposable scratch pair against canonical cross-day
history before creating canonical target directories; it then repeats pair QA
under the canonical publication lock. Runtime/window checks occur before the
scratch step. Existing targets require explicit force/repair authorization.
Pair replacement retains the existing ordinary-I/O rollback and hash/generation
verification; it does not claim crash atomicity across two files or SQLite.

This release does not authorize the missing 2026-10-07 Daily. Its reason remains
PUBLIC_AUTOMATION_RUNTIME_CODE_BLOCKED. LIVE automation migration and unchanged
schedules must be independently verified before declaring recovery ready.
