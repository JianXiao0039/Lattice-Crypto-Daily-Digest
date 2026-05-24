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

## 本地 Codex 自动化后自动推送 GitHub

Codex 本地自动化可以直接调用：

```powershell
.\scripts\run_daily_digest_and_push.ps1
```

也可以双击或从其他调度器调用：

```cmd
scripts\run_daily_digest_and_push.cmd
```

脚本会自动定位项目根目录，先执行 `git pull --rebase --autostash origin main`，再运行日报生成和 `python -m pytest`。只有两步都成功后，脚本才会执行 `git add digests data papers.db`、提交 `daily lattice digest: YYYY-MM-DD` 并 `git push origin main`。

运行前需要确认本地 `git push` 已经能通过 Clash 代理访问 GitHub。如果已经配置过以下内容，无需重复配置：

```powershell
git config --global http.proxy http://127.0.0.1:7897
git config --global https.proxy http://127.0.0.1:7897
git config --global http.version HTTP/1.1
```

如果 push 失败，先手动检查：

```powershell
git ls-remote https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git
git push
```

脚本不会暂存 `.env`、`memory.md`、`.tmp/`、`.vscode/`、`cache/`、`.cache/`、`.history/` 或 pytest 临时目录。
