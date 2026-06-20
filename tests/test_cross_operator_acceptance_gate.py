from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_acceptance_gate_rejects_not_run_operators() -> None:
    text = (ROOT / "docs/operations/cross_operator_fallback_acceptance_gate_v0.1.md").read_text(
        encoding="utf-8"
    )
    assert "Not-Run Rule" in text
    assert "Never classify a not-run operator as ready" in text
    assert "blocked_by_missing_operator" in text
    assert "insufficient_evidence" in text


def test_acceptance_gate_requires_codex_review_and_real_evidence() -> None:
    text = (ROOT / "docs/operations/cross_operator_fallback_acceptance_gate_v0.1.md").read_text(
        encoding="utf-8"
    )
    for phrase in [
        "it actually ran the common dry-run task set",
        "Codex reviewed its paste-back package",
        "reported `command_unavailable` honestly",
        "reported source health using the common categories",
        "produced the common final report sections",
    ]:
        assert phrase in text


def test_codex_prompt_is_comparator_not_merely_runner() -> None:
    text = (ROOT / "docs/operations/codex_dry_run_prompt_v0.1.md").read_text(encoding="utf-8")
    assert "cross-operator comparator" in text
    assert "Classify drift" in text or "classify drift" in text
    assert "must not claim cross-operator parity unless" in text
    assert "not_run_drift" in text

