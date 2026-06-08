# Daily Digest Three-Run Stability Protocol v0.1

Status: public manual stability-check protocol.

# Goal

Use three bounded manual runs to distinguish:

- probe-level reachability,
- manual recovery viability,
- weekly handoff reliability.

# Run 1: Probe-only Health Check

```powershell
python scripts\probe_source_connectivity.py
```

Purpose:

- classify network/source/API readiness;
- distinguish DNS/TLS/rate-limit/auth/parser classes.

# Run 2: Manual Recovery Daily Run

```powershell
python -m lattice_digest.run --since 7d --output markdown,json --send none --retry-failed-sources --include-latest-sources
```

Purpose:

- verify failed-attempt guard recovery path;
- check whether bounded manual retry restores usable daily source health.

# Run 3: Weekly Handoff Replay

Preferred working command:

```cmd
scripts\run_weekly_handoff.bat
```

Alternative if available:

```powershell
python -m lattice_digest.weekly_handoff --latest
```

Purpose:

- verify weekly handoff does not overclaim when daily inputs are degraded;
- ensure empty or sparse weekly input is explained.

# Interpretation Rules

- `0 records + all-red` => source-starved
- non-empty daily with yellow sources => degraded-but-usable
- empty weekly handoff with degraded source history => incomplete coverage, not “no papers”
- IACR `cache_hit` is valid latest recovery evidence

# Forbidden Actions

- no scheduler
- no background retry loop
- no git add/commit/push/tag
- no private workspace writes
