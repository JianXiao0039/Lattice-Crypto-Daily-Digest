# lattice-crypto-daily-digest

Daily paper radar for lattice cryptography. The project fetches records from API/RSS/OAI-friendly sources, removes non-cryptographic lattice papers, deduplicates overlapping records, ranks them into A/B/C/D relevance labels, and emits a Chinese daily digest.

## Quick Start

```powershell
python -m pip install -e ".[dev]"
python -m lattice_digest.run --since 36h --dry-run
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

The normal run writes:

- `digests/YYYY-MM-DD.md`
- `data/YYYY-MM-DD.json`
- `papers.db`

Dry-run prints what would happen and does not write output files.

