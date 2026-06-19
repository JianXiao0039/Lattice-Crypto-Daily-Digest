# Codex / DeepSeek-Claude / Kimi Command Matrix v0.1

Status: `operator_command_matrix_ready`.

Use PowerShell unless the operator explicitly chooses CMD or Git Bash and translates paths correctly.

| Operation | Codex command | DeepSeek-Claude command | Kimi Code command | Status | Expected artifacts | Failure interpretation | Codex review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pre-run checks | `git status -sb`; `python --version`; `python -m lattice_digest.workflow status`; `python -m lattice_digest.workflow doctor` | same | same | allowed | terminal report | `workflow status` unavailable is reportable; `doctor` failure blocks run | no, unless failure changes code |
| Daily latest | `python -m lattice_digest.run --since 36h --output markdown,json --send none` | same | same | allowed | `data/YYYY-MM-DD.json`, `digests/YYYY-MM-DD.md`, `papers.db` | source-starved is degraded evidence, not quiet day | yes if code changes |
| Daily specific-date backfill | `python -m lattice_digest.run --date YYYY-MM-DD --output markdown,json --send none` | same | same | caution | date-specific JSON/Markdown | do not overwrite authoritative artifacts without reporting | yes if output is release evidence |
| Specific time range | `python -m lattice_digest.run --since 7d --output markdown,json --send none` | same | same | caution | range-derived latest artifacts | do not invent unsupported `--start` / `--end` flags | no if command succeeds |
| Weekly dry-run | `python -m lattice_digest.workflow weekly --low-load --skip-hygiene` | same | same | allowed | dry-run plan | dry-run failure blocks execute | no |
| Weekly execute | `python -m lattice_digest.workflow weekly --low-load --skip-hygiene --execute` | same | same | caution | `data/weekly/YYYY-Www.json`, `digests/weekly/YYYY-Www.md` | missing days must be reported | yes if used as release evidence |
| Monthly run | `python -m lattice_digest.monthly_synthesis --month YYYY-MM` | same | same | allowed | `data/monthly/YYYY-MM.json`, `digests/monthly/YYYY-MM.md` | missing daily files/source-starved status must be explicit | yes if code changes |
| Full manual run | command sequence in `manual_full_run_sop_v0.1.md` | same sequence | same sequence | caution | Daily/Weekly/Monthly, probes, exports, audits | not automation; stop on unsafe failures | yes for nontrivial warnings |
| Source-health probe | `python scripts\probe_source_health.py --low-load` | same | same | allowed | sanitized probe output | degraded source is explicit caveat, not proof of no papers | yes if classification logic changes |
| Durable verification | `python scripts\verify_durable_artifacts.py --date YYYY-MM-DD --week YYYY-Www --month YYYY-MM` | same | same | allowed | verification JSON/terminal status | missing artifact blocks durable evidence | yes if verifier changes |
| Reading queue export | `python scripts\export_reading_queue.py --latest` | same | same | allowed | reading queue export/state | no manual annotation fields required | yes if schema changes |
| Obsidian export | `python scripts\export_obsidian_notes.py --latest` | same | same | allowed | repository-local Obsidian notes | no write to `D:\ResearchOS` | yes if template changes |
| Monthly quality audit | `python scripts\audit_monthly_rationale_quality.py --latest` | same | same | allowed | `audits/monthly-quality/YYYY-MM.*` | keyword-only or missing TODO_VERIFY is quality failure | yes if audit script changes |
| Bilingual rationale quality audit | same monthly audit plus top-paper Markdown review | same | same | allowed | monthly audit plus report | missing `中文：` / `English:` for top papers is warning or blocker by policy | yes if rendering changes |
| Test suite | `scripts\run_project_tests.bat` | same | same | caution | test result | failing tests require Codex review before code changes | yes |
| Release hygiene | `python scripts\check_release_hygiene.py` | same | same | caution | hygiene output | hygiene failure blocks release evidence | yes |
| Final report | use `manual_operator_report_template_v0.1.md` | same | same | required | report text | missing report means insufficient evidence | no |

DeepSeek-Claude and Kimi Code are fallback manual runners and not release owners.

No row authorizes automatic git writes, tag operations, background services, or private path access.
