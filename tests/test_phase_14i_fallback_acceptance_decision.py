from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_acceptance_decision_rejects_missing_operator_evidence() -> None:
    text = (ROOT / "docs/reports/phase-14i-fallback-acceptance-decision.md").read_text(
        encoding="utf-8"
    )
    assert "deepseek_claude_fallback_blocked_by_missing_evidence" in text
    assert "kimi_code_fallback_blocked_by_missing_evidence" in text
    assert "cross_operator_parity_blocked_by_missing_operator_evidence" in text
    assert "Codex review is required" in text


def test_after_14i_policy_keeps_fallback_use_blocked() -> None:
    text = (ROOT / "docs/operations/cross_operator_fallback_use_policy_after_14i_v0.1.md").read_text(
        encoding="utf-8"
    )
    assert "fallback_use_blocked_until_actual_runs" in text
    assert "Codex remains the primary engineering" in text
    assert "blocked by missing evidence" in text
    assert "Codex confirms no boundary drift" in text

