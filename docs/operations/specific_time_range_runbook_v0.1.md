# Specific Time Range Runbook v0.1

## Supported Since-Based Runs

The Daily CLI supports `--since` windows:

```powershell
python -m lattice_digest.run --since 36h --output markdown,json --send none
python -m lattice_digest.run --since 7d --output markdown,json --send none
```

## Supported Exact-Date Runs

```powershell
python -m lattice_digest.run --date YYYY-MM-DD --output markdown,json --send none
```

## Weekly Date Range

The Weekly workflow supports explicit date bounds:

```powershell
python -m lattice_digest.workflow weekly --from-date YYYY-MM-DD --to-date YYYY-MM-DD --low-load --skip-hygiene
python -m lattice_digest.workflow weekly --from-date YYYY-MM-DD --to-date YYYY-MM-DD --low-load --skip-hygiene --execute
```

## Unsupported Daily Flags

The current Daily CLI help does not expose `--start` / `--end`. Do not invent those flags. Use `--since` or exact `--date`.

## Review

For range runs, report the target interval, output date, missing days, and source-health reliability. Do not infer success from command completion alone.
