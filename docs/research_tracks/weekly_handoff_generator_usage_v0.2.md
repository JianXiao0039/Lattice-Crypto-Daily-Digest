# Weekly Handoff Generator Usage v0.2

Status: public manual-use guide for the hardened standalone generator.

# Purpose

Generate stable weekly research-triage and handoff packet drafts from existing weekly JSON.

The generator is:

- manual-only;
- offline;
- deterministic;
- additive;
- dry-run capable;
- separate from daily/weekly workflow semantics.

It does not fetch sources, recalculate ranking, modify existing weekly files, synchronize ResearchArtifacts, or write private PhD application material.

# Environment Check

Use the validated project environment:

```powershell
python --version
python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print(ZoneInfo('Asia/Singapore'))"
```

# Commands

## Preview latest week

```powershell
python -m lattice_digest.weekly_handoff --latest --dry-run
```

## Generate latest week

```powershell
python -m lattice_digest.weekly_handoff --latest
```

## Generate a specific week

```powershell
python -m lattice_digest.weekly_handoff --weekly-json data\weekly\2026-W23.json
```

## Custom input directory

```powershell
python -m lattice_digest.weekly_handoff --latest --weekly-data-dir data\weekly
```

## Custom public output directory

```powershell
python -m lattice_digest.weekly_handoff --latest --output-dir handoffs\weekly
```

There is no `scripts\generate_weekly_handoff.py` wrapper. Use the module command above.

# Output

Default paths:

```text
handoffs/weekly/YYYY-Www-handoff-packets.json
handoffs/weekly/YYYY-Www-handoff-packets.md
```

`handoffs/` is ignored by git and should not be committed by default.

# Review Procedure

1. Review track and action counts.
2. Review every `handoff_after_verify` packet.
3. Confirm the lattice/PQC anchor from the original source.
4. Review verification burden and overclaim risk.
5. Preserve all TODO_VERIFY items and non-claims.
6. Decide manually whether an item should be copied into ResearchArtifacts.
7. Leave generic/noise records excluded.

# Tracks

- `module_sis_chameleon_hash`
- `xingye_lu_bridge`
- `ai4lattice_longline`
- `mlkem_mldsa_background`
- `privacy_registration_watchlist`
- `excluded_noise`

# Actions

- `handoff_now`
- `handoff_after_verify`
- `keep_in_radar`
- `backlog`
- `exclude`

Metadata-only Module-SIS or public Xingye bridge candidates should normally remain `handoff_after_verify`.

# Safety Boundaries

The generator refuses to write into:

- `PhD_Application`;
- `.git`.

It does not automatically write into:

- `D:\ResearchArtifacts\module-sis-chameleon-hash`.

Do not redirect output to private or Git-internal paths.

# Validation

Run project-scoped tests:

```powershell
python -m pytest tests\test_weekly_handoff.py --basetemp=.pytest_tmp
scripts\run_project_tests.bat
```

Never use bare `python -m pytest`.

# Non-Claims

Generated packets are triage records only. They are not:

- security proofs;
- novelty claims;
- working-construction claims;
- PI-topic claims;
- publication claims.

# Known Limitations

- Classification uses deterministic metadata/evidence rules.
- Original papers are not read automatically.
- Source tags may be broad or imperfect.
- Source health does not guarantee complete literature coverage.
- Scores are handoff-policy scores, not security judgments or existing relevance scores.

