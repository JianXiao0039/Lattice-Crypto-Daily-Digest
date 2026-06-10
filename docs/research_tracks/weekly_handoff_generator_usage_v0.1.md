# Weekly Handoff Generator Usage v0.1

Status: public manual-use documentation.

# Purpose

Generate structured weekly research-triage and handoff packets from existing weekly JSON files.

The generator:

- reads existing weekly JSON only;
- does not fetch sources;
- does not modify ranking;
- does not modify daily/weekly artifacts;
- does not write ResearchArtifacts;
- refuses `PhD_Application` output paths;
- creates no scheduler or background task.

# Commands

## Latest week

```powershell
python -m lattice_digest.weekly_handoff --latest
```

Default output:

```text
handoffs/weekly/YYYY-Www-handoff-packets.json
handoffs/weekly/YYYY-Www-handoff-packets.md
```

## Dry-run

```powershell
python -m lattice_digest.weekly_handoff --latest --dry-run
```

Dry-run prints the planned paths and writes nothing.

## Specific weekly JSON

```powershell
python -m lattice_digest.weekly_handoff --weekly-json data\weekly\2026-W23.json
```

## Custom weekly data directory

```powershell
python -m lattice_digest.weekly_handoff --latest --weekly-data-dir data\weekly
```

## Custom output directory

```powershell
python -m lattice_digest.weekly_handoff --latest --output-dir handoffs\weekly
```

# Output Review

Review these fields before using a packet:

- track;
- action label;
- lattice/PQC anchor evidence;
- Module-SIS and chameleon-hash relevance scores;
- verification burden;
- overclaim risk;
- intended ResearchArtifacts target;
- TODO_VERIFY;
- non-claims.

`handoff_after_verify` means the item must be read and verified before artifact intake.

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

# Safety Rules

- Do not treat packet scores as security judgments.
- Do not treat packets as novelty claims.
- Do not treat metadata as original-paper verification.
- Do not copy private application material into packets.
- Do not manually redirect output into `PhD_Application`.
- Do not commit generated `handoffs/` by default.
- Do not create scheduled automation.

# Manual Review Checklist

- [ ] Confirm the paper title and identifier.
- [ ] Read the original paper before accepting technical claims.
- [ ] Confirm the lattice/PQC anchor.
- [ ] Confirm the intended artifact use.
- [ ] Keep TODO_VERIFY visible.
- [ ] Preserve every non-claim.
- [ ] Reject generic/noise candidates.
- [ ] Decide manually whether to copy a packet into ResearchArtifacts.

# Limitations

- Keyword/evidence policy can make mistakes.
- Source-health caveats do not guarantee complete coverage.
- Public Xingye bridge packets are technical bridge records only; they contain no professor-specific verified facts.
- ResearchArtifacts mirroring is not implemented.

