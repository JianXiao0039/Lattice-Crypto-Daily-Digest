from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_DOCS = [
    "docs/reports/phase-14i-second-cross-operator-dry-run.md",
    "docs/reports/phase-14i-codex-dry-run-evidence.md",
    "docs/reports/phase-14i-deepseek-claude-real-dry-run-log.md",
    "docs/reports/phase-14i-kimi-code-real-dry-run-log.md",
    "docs/reports/phase-14i-cross-operator-final-comparison.md",
    "docs/reports/phase-14i-fallback-acceptance-decision.md",
    "docs/reports/phase-14i-operator-drift-remediation.md",
    "docs/reports/phase-14i-paper-radar-core-invariant-audit.md",
    "docs/operations/cross_operator_second_dry_run_result_v0.1.md",
    "docs/operations/deepseek_claude_fallback_acceptance_status_v0.1.md",
    "docs/operations/kimi_code_fallback_acceptance_status_v0.1.md",
    "docs/operations/cross_operator_fallback_use_policy_after_14i_v0.1.md",
]


def test_phase_14i_docs_exist() -> None:
    missing = [path for path in REQUIRED_DOCS if not (ROOT / path).exists()]
    assert missing == []


def test_fallback_logs_explicitly_mark_missing_paste_back() -> None:
    deepseek = (ROOT / "docs/reports/phase-14i-deepseek-claude-real-dry-run-log.md").read_text(
        encoding="utf-8"
    )
    kimi = (ROOT / "docs/reports/phase-14i-kimi-code-real-dry-run-log.md").read_text(
        encoding="utf-8"
    )
    assert "missing_paste_back" in deepseek
    assert "deepseek_claude_fallback_blocked_by_missing_evidence" in deepseek
    assert "not_run_drift" in deepseek
    assert "missing_paste_back" in kimi
    assert "kimi_code_fallback_blocked_by_missing_evidence" in kimi
    assert "not_run_drift" in kimi

