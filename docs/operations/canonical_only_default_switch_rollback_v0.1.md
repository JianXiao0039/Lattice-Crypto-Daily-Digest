# Canonical-Only Default Switch Rollback v0.1

## Purpose

This plan describes the one-change rollback for the Phase 14S-A working-tree
fallback-default switch.

## Previous Code Behavior

Before Phase 14S-A:

- unset variable permits fallback;
- explicit false values `0`, `false`, `no`, `off` disable fallback;
- all other explicit values enable fallback;
- explicit function argument overrides the environment.

## New Code Behavior

After Phase 14S-A:

- unset variable disables fallback;
- explicit false values `0`, `false`, `no`, `off` disable fallback;
- explicit true values `1`, `true`, `yes`, `on`, `compat` enable fallback;
- invalid environment values do not enable fallback;
- explicit function argument still overrides the environment.

## Rollback Diff Description

Revert only `legacy_fallback_allowed()` in `src/lattice_digest/artifact_paths.py`
so that a missing `LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK` value returns `True`.

No artifact path changes are required.
No source behavior changes are required.
No artifact data changes are required.
No Git tracking changes are required.
No archive state changes are required.

## Emergency Process-Level Compatibility

Before a code rollback, a single process can explicitly enable compatibility:

```powershell
$env:LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK = "1"
```

Equivalent compact notation:

```text
LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK=1
```

This must remain process-scoped. Do not set a persistent User or Machine
environment variable.

## Rollback Validation Commands

```powershell
D:\CyberSecurity\Python315\python.exe -m pytest tests\test_phase_14s_a_default_switch.py tests\test_phase_14s_a_explicit_compatibility.py -q
D:\CyberSecurity\Python313\python.exe scripts\check_release_hygiene.py
git diff --check
```

Do not run Git write operations as part of rollback validation.
