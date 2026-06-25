# External Pytest Basetemp Policy v0.1

## Purpose

Manual and release-gate pytest runs must keep pytest basetemp output outside the repository. Repository-local basetemp roots can leave fixture output, symlink entries, or reparse points visible to Git on Windows.

## Mandatory External Temp Root

Use this manually controlled root:

```text
D:\Code\CodexProjects_pytest_runs
```

The root is outside:

```text
D:\Code\CodexProjects\lattice-crypto-daily-digest
```

Do not create pytest basetemp directories under the repository root for new validation evidence.

## Required Command Convention

Every pytest command must pass an explicit, unique external basetemp:

```text
--basetemp "D:\Code\CodexProjects_pytest_runs\<phase>_<unique-run-id>"
```

Use scoped test lists for release gates unless a phase explicitly authorizes a full host suite.

## Unique Run IDs

Every invocation must use a fresh run directory. Recommended identifiers include the phase name plus a timestamp, GUID, or short nonce.

Do not reuse a basetemp from a prior run.

## Concurrent Run Safety

Concurrent test runs must not share a basetemp. Each process gets its own unique directory under the external root.

## Failure Preservation

Failed external runs may be retained for diagnosis. Preserved output must remain outside the repository unless a later phase explicitly approves copying a narrow evidence excerpt.

## Manual Cleanup Only

Cleanup is manual and path-scoped. Do not use broad repository cleanup commands to recover from pytest temp failures.

Do not create scheduled cleanup, services, watchers, polling loops, or background automation.

## Prohibited Repository-Local Basetemp

Do not use repository-local basetemp roots for new validation runs, including:

- `.pytest_tmp`
- `.pytest_tmp_run_<id>`
- `.pytest_host_<id>`
- `.phase*_test_tmp`

Existing repository-local temporary roots are historical cleanup subjects only. Do not delete or traverse reparse entries without a separate cleanup review.

## Broad Pytest Limitation

Broad unscoped pytest is not authoritative while untracked test files remain in the worktree. Scoped test lists remain the release gate unless a phase explicitly authorizes and records a full host suite.

## Examples

Focused test run:

```powershell
D:\CyberSecurity\Python315\python.exe -m pytest tests\test_source_health.py --basetemp "D:\Code\CodexProjects_pytest_runs\phase15b_source_health_<unique-run-id>"
```

Full project test run when explicitly authorized:

```powershell
D:\CyberSecurity\Python315\python.exe -m pytest tests --basetemp "D:\Code\CodexProjects_pytest_runs\phase15b_full_<unique-run-id>"
```

## TODO_VERIFY

- Update any older active runbook that still recommends repository-local `.pytest_tmp` before using it as release evidence.
- Keep external temp cleanup manual until a separate reviewed cleanup policy is authorized.
