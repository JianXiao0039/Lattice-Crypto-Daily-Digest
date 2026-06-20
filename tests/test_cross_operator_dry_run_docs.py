from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_DOCS = [
    "docs/operations/cross_operator_dry_run_drill_v0.1.md",
    "docs/operations/codex_deepseek_kimi_dry_run_task_set_v0.1.md",
    "docs/operations/cross_operator_output_comparison_template_v0.1.md",
    "docs/operations/deepseek_claude_dry_run_prompt_v0.1.md",
    "docs/operations/kimi_code_dry_run_prompt_v0.1.md",
    "docs/operations/codex_dry_run_prompt_v0.1.md",
    "docs/operations/operator_divergence_remediation_policy_v0.1.md",
    "docs/operations/cross_operator_fallback_acceptance_gate_v0.1.md",
    "docs/reports/phase-14g-cross-operator-dry-run-drill.md",
    "docs/reports/phase-14g-codex-dry-run-log.md",
    "docs/reports/phase-14g-deepseek-claude-dry-run-log.md",
    "docs/reports/phase-14g-kimi-code-dry-run-log.md",
    "docs/reports/phase-14g-cross-operator-output-comparison.md",
    "docs/reports/phase-14g-operator-divergence-and-remediation.md",
    "docs/reports/phase-14g-paper-radar-core-invariant-audit.md",
]


def test_phase_14g_dry_run_docs_exist() -> None:
    missing = [path for path in REQUIRED_DOCS if not (ROOT / path).exists()]
    assert missing == []


def test_phase_14g_main_report_marks_missing_operators_not_run() -> None:
    report = (ROOT / "docs/reports/phase-14g-cross-operator-dry-run-drill.md").read_text(encoding="utf-8")
    assert "DeepSeek-Claude: not run" in report
    assert "Kimi Code: not run" in report
    assert "cross_operator_dry_run_blocked_by_missing_operator" in report
    assert "do not claim full parity" not in report.lower()

