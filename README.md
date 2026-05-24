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

Optional `.env` values such as `CONTACT_EMAIL`, `SEMANTIC_SCHOLAR_API_KEY`, `DIGEST_SINCE`, `DIGEST_OUTPUT`, and `DIGEST_SEND` are documented in `.env.example`. The current CLI still takes `--since`, `--output`, and `--send` from command-line arguments, so automation should pass them explicitly.

Network/API failures are non-fatal: sources that return 429, SSL, or transient network errors are recorded as warnings while the run continues with any successful sources. The system still writes an empty Chinese digest when no A/B/C papers pass the conservative lattice-cryptography filters.

## Local Run

Run the same pipeline locally with:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m lattice_digest.run --since 36h --output markdown,json --send none
python scripts/send_latest_digest_email.py
```

The email script reads `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM`, and `MAIL_TO` from the environment and sends the newest `digests/YYYY-MM-DD.md` body as plain text. Do not commit `.env` or real SMTP/API secrets.

## GitHub Actions

The workflow `.github/workflows/daily.yml` runs every day at `01:17 UTC` (about `09:17` in Beijing/Singapore time) and can also be started manually from GitHub Actions with `workflow_dispatch`.

Configure these repository secrets before enabling email delivery:

- `CONTACT_EMAIL`
- `SEMANTIC_SCHOLAR_API_KEY` (optional, improves Semantic Scholar quota)
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `MAIL_FROM`
- `MAIL_TO`

The workflow checks out the repository, installs Python 3.11, runs the digest command, runs tests, sends the latest Markdown digest by email, then commits `digests`, `data`, and `papers.db` back to `main` if generated artifacts changed.

To verify delivery, open the latest workflow run and check the `Send email` step for `sent email to ...`. SMTP/API failures appear in the GitHub Actions log; the digest command itself treats 429, SSL, and transient network failures as warnings and continues with other sources.
