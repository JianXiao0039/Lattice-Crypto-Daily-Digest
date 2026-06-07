# Weekly Public Synthesis with Handoff v0.1

Status: public manual workflow guide.

# Purpose

Describe how to pair weekly public synthesis with weekly handoff packet generation without changing workflow semantics.

# Design

Weekly synthesis remains the public research summary layer.

Weekly handoff is a follow-up triage layer that reads existing weekly JSON and produces handoff packets for manual review.

# Recommended Manual Order

1. Run or inspect weekly synthesis:

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
```

If writing weekly outputs is intended, use the existing workflow command with explicit `--execute` after reviewing the dry-run plan.

2. Generate handoff packets:

```powershell
python -m lattice_digest.weekly_handoff --latest
```

or:

```powershell
scripts\run_weekly_handoff.bat
```

3. Review:

```text
handoffs/weekly/YYYY-Www-handoff-packets.md
```

# Track Review Order

1. `module_sis_chameleon_hash`
2. `xingye_lu_bridge`
3. `ai4lattice_longline`
4. `mlkem_mldsa_background`
5. `privacy_registration_watchlist`
6. `excluded_noise`

# Action Review Order

1. `handoff_now`
2. `handoff_after_verify`
3. `keep_in_radar`
4. `backlog`
5. `exclude`

# Boundary

This guide does not make weekly synthesis automatically generate handoff packets.

Daily public digest remains discovery-oriented. Source recovery remains separate. ResearchArtifacts intake remains manual.

# TODO_VERIFY

- Whether future weekly reports should include a lightweight handoff summary.
- Whether original-paper verification status should become a structured field.
- Whether handoff scoring should be adjusted after manual pilot review.

