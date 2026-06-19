# Phase 14C Cross-Operator Command Parity Review

Status: `codex_deepseek_kimi_parity_ready`.

The command matrix covers:

- pre-run checks;
- Daily latest;
- Daily specific-date backfill;
- specific time range using supported `--since`;
- Weekly dry-run;
- Weekly execute;
- Monthly run;
- Full manual run;
- source-health probe;
- durable artifact verification;
- reading queue export;
- Obsidian export;
- monthly quality audit;
- bilingual rationale quality audit;
- test suite;
- release hygiene;
- final operation report.

The same manual commands are documented for Codex, DeepSeek-Claude, and Kimi Code. DeepSeek-Claude and Kimi Code are fallback runners, not release owners.

Any code, test, source-health classification, verifier, runbook, or release-gate change requires Codex review.
