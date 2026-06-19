# Phase 14D Reading Queue / Obsidian Usability and Operator Prompt Safety

## Decision

- Reading queue usability: `reading_queue_usability_improved`.
- Obsidian usability: `obsidian_scaffold_improved`.
- Operator prompt safety: `codex_deepseek_kimi_prompt_safety_ready`.
- Cross-operator compatibility: `cross_operator_compatibility_ready_with_codex_review_required`.
- Production gate: `eligible_for_v0_6_reading_usability`.

## Dependency Status

Phase 14C outputs are present and were used for operator parity and fallback policy.

Phase 14A / 14B outputs are present and were used for monthly quality and bilingual rationale policy.

## Implementation Summary

- Reading queue records now include normalized `research_direction`, bilingual rationale fields, TODO_VERIFY categories, and source-health caveats.
- Reading queue dashboard export now includes action, direction, and TODO_VERIFY category views.
- Obsidian paper notes now include Radar Decision, Chinese rationale, English rationale, Direction Mapping, Deep Reading Checklist, Claim Verification, Research Use, and Links.
- Route prompt safety policy and standardized operator prompt header were added.
- DeepSeek-Claude and Kimi Code remain fallback runners/reviewers with Codex review required for code changes.

No ranking, source fetching, taxonomy, query expansion, negative keyword behavior, manual annotation workflow, external LLM call, automation, or release/tag operation was introduced.

## Validation Summary

- Python and doctor checks passed on the local interpreter, Python 3.15.0b2.
- Package version check returned 0.4.1.
- Compile checks passed for `reading_queue.py`, `obsidian_scaffold.py`, `export_reading_queue.py`, and `export_obsidian_notes.py`.
- Phase 14D focused tests passed: 10 tests.
- Existing reading queue / Obsidian compatibility tests passed: 34 tests.
- `python scripts/export_reading_queue.py --latest` passed and wrote repository-local reading queue dashboards.
- `python scripts/export_obsidian_notes.py --latest` passed and refreshed repository-local Obsidian paper notes.
- `scripts/run_project_tests.bat` passed: 680 tests.
- `python scripts/check_release_hygiene.py` passed.
- `git diff --check` and `git diff --cached --check` passed.

## File Substitution

The requested `src/lattice_digest/obsidian_export.py` file is not present in this repository. The actual Obsidian implementation is `src/lattice_digest/obsidian_scaffold.py`, and Phase 14D updated and validated that file instead.

## Safety Confirmation

- No private PhD, ResearchArtifacts, or ResearchOS path was read or written.
- No manual annotation workflow, human-gold metric workflow, or shadow classifier productionization was introduced.
- No external LLM runtime or network paper fetching outside existing radar commands was added.
- No background automation, scheduled task, watcher, cron job, startup task, or service was created.
- No `git add`, `git commit`, `git push`, or `git tag` command was executed.
