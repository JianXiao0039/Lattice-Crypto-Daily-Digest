from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_final_comparison_has_three_operator_columns() -> None:
    text = (ROOT / "docs/reports/phase-14i-cross-operator-final-comparison.md").read_text(
        encoding="utf-8"
    )
    assert "| Field | Codex | DeepSeek-Claude | Kimi Code |" in text
    assert "Command Parity" in text
    assert "Artifact Parity" in text
    assert "Source-Health Interpretation Parity" in text
    assert "Monthly Audit / Rationale Quality Parity" in text


def test_final_comparison_blocks_parity_when_fallback_evidence_missing() -> None:
    text = (ROOT / "docs/reports/phase-14i-cross-operator-final-comparison.md").read_text(
        encoding="utf-8"
    )
    assert "cross_operator_parity_blocked_by_missing_operator_evidence" in text
    assert "DeepSeek-Claude and Kimi Code command evidence is missing" in text
    assert "fallback operators because no paste-back package was provided" in text

