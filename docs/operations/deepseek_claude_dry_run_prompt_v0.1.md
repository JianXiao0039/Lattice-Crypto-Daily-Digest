# DeepSeek-Claude Dry Run Prompt v0.1

Project root: `D:\Code\CodexProjects\lattice-crypto-daily-digest`

Current active route: only the public paper-radar route is active.

Operator: DeepSeek-Claude.

Operator role: emergency fallback runner/reviewer. DeepSeek-Claude is not the release owner. It must not modify code unless explicitly authorized. If code changes appear necessary, stop and request Codex review.

This prompt is self-contained. Do not rely on memory as factual evidence. Use only the commands and local files in this prompt and the repository.

## DeepSeek-Claude Boundary Self-Check

- Working directory:
- I will not read or write PhD_Application:
- I will not read or write ResearchArtifacts:
- I will not write ResearchOS:
- I will not run git add/commit/push/tag:
- I will not create automation:
- I will not modify ranking/source/taxonomy:
- I will ask for Codex review before any code change:
- I will report unavailable commands honestly:

## Forbidden

- Read or write `D:\Code\CodexProjects\PhD_Application`.
- Read or write `D:\ResearchArtifacts`.
- Write `D:\ResearchOS`.
- Run `git add`, `git commit`, `git push`, or `git tag`.
- Create, delete, move, or recreate release tags.
- Create Windows Task Scheduler tasks, cron jobs, startup tasks, watchers, background services, or automatic future runs.
- Modify source fetchers, ranking scores, ranking thresholds, taxonomy semantics, query expansion, or negative keyword behavior.
- Create manual annotation workflows, human-gold workflows, or shadow classifier productionization.
- Add external LLM runtime calls.
- Print secrets or `.env` contents.
- Invent command success. If a command is missing or fails to run, report `command_unavailable` or the actual failure.

Compatibility wording: do not run `git add`, `git commit`, `git push`, or `git tag`.

## Exact CMD Command Sequence

Run from CMD:

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
git status -sb
python --version
python -m lattice_digest.workflow doctor
python -m lattice_digest.workflow status
python -m lattice_digest.run --since 36h --output markdown,json --send none
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
python -m lattice_digest.monthly_synthesis --month 2026-06
python scripts\probe_source_health.py --low-load
python scripts\verify_durable_artifacts.py --date 2026-06-15 --week 2026-W25 --month 2026-06
python scripts\export_reading_queue.py --latest
python scripts\export_obsidian_notes.py --latest
python scripts\audit_monthly_rationale_quality.py --latest
git diff --check
git diff --cached --check
git status -sb
```

If a command is unavailable, do not invent success. Record:

```text
command_unavailable: <command>
reason: <observed reason>
```

## Source-Health Classification Table

Use these categories:

- arXiv HTTP 429: `rate_limited`.
- DBLP TLS/SSL failure: `ssl_failure` or `tls`.
- IACR failed/0: source failure or recovery failure, not "no relevant papers".
- Semantic Scholar missing key: `missing_key`; HTTP 401/403: `auth_failure`; HTTP 429: `rate_limited`; timeout/network failure: `timeout` or `network_error`; zero valid result: `empty_response`.
- OpenAlex zero valid result: `empty_response` if request succeeded; `network_error` if request failed.
- Crossref zero valid result: `empty_response` or `query_mismatch` if request succeeded; network failure otherwise.

## Normalized Command List for Cross-Operator Comparison

Use these normalized strings when comparing outputs across operators:

- `python -m lattice_digest.run --since 36h --output markdown,json --send none`
- `python -m lattice_digest.workflow weekly --low-load --skip-hygiene`
- `python -m lattice_digest.monthly_synthesis --month 2026-06`
- `python scripts/probe_source_health.py --low-load`
- `python scripts/verify_durable_artifacts.py --date 2026-06-15 --week 2026-W25 --month 2026-06`
- `python scripts/export_reading_queue.py --latest`
- `python scripts/export_obsidian_notes.py --latest`
- `python scripts/audit_monthly_rationale_quality.py --latest`
- `git diff --check`
- `git diff --cached --check`
- `git status -sb`

## Final Report Sections

Produce the final report in Chinese with these exact sections:

- Operator
- Boundaries
- Commands Run
- Artifacts Generated
- Source Health
- Radar Output Quality
- Durable Artifact Status
- Failures / Warnings
- Next Recommended Operator
- Final Status

## Paste-Back Block for Codex

After the final report, include:

```text
BEGIN FALLBACK_OPERATOR_PASTE_BACK
Operator:
Tool / model:
Date/time:
Working directory:
Boundary self-check:
Commands run:
Commands unavailable:
Artifacts generated:
Source-health table:
Monthly audit result:
Reading queue / Obsidian result:
Failures / warnings:
Git status before:
Git status after:
Final status:
Request for Codex review:
END FALLBACK_OPERATOR_PASTE_BACK
```
