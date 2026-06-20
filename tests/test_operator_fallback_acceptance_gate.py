from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fallback_acceptance_gate_requires_safety_and_same_task_set() -> None:
    text = (ROOT / "docs/operations/cross_operator_fallback_acceptance_gate_v0.1.md").read_text(
        encoding="utf-8"
    )
    for phrase in [
        "avoids private paths",
        "avoids `git add`, `git commit`, `git push`, and `git tag`",
        "avoids background automation",
        "avoids source fetcher, ranking, taxonomy, query expansion, and negative keyword changes",
        "runs or reports the same task set",
        "reports degraded source health explicitly",
        "uses the shared final report sections",
    ]:
        assert phrase in text


def test_divergence_policy_requires_codex_review_after_boundary_risk() -> None:
    text = (ROOT / "docs/operations/operator_divergence_remediation_policy_v0.1.md").read_text(
        encoding="utf-8"
    )
    assert "Boundary Violation" in text
    assert "stop trusting that operator for fallback use" in text
    assert "require Codex review before future use" in text
    assert "arXiv 429 not classified as rate_limited" in text
    assert "IACR failed/0 interpreted as no relevant papers" in text

