# Manual Specific-Date and Time-Range SOP v0.1

Status: `specific_date_and_range_sop_ready`.

## Exact Date

Before running, check whether the target artifacts already exist:

```powershell
Test-Path data\YYYY-MM-DD.json
Test-Path digests\YYYY-MM-DD.md
```

Run:

```powershell
python -m lattice_digest.run --date YYYY-MM-DD --output markdown,json --send none
```

After running, verify:

```powershell
python scripts\verify_durable_artifacts.py --date YYYY-MM-DD --week YYYY-Www --month YYYY-MM
```

Do not overwrite authoritative artifacts without reporting the existing files and the reason.

## Supported Time Range

The documented supported range form is `--since`:

```powershell
python -m lattice_digest.run --since 7d --output markdown,json --send none
```

If explicit `--start` / `--end` flags are not supported by the CLI, do not invent them. Use `--since` or a manually reviewed exact-date sequence.

Do not turn the exact-date or range workflow into background automation.
