from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKS = ROOT / "docs" / "research_tracks"
OPS = ROOT / "docs" / "operations"


def test_cross_operator_result_consistency_policy_exists() -> None:
    path = TRACKS / "v0.6_codex_deepseek_kimi_result_consistency_policy_v0.1.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "compatible artifacts" in text
    assert "final operation report" in text
    assert "cannot silently change final release outcome" in text


def test_manual_operator_report_template_is_shared() -> None:
    text = (OPS / "manual_operator_report_template_v0.1.md").read_text(encoding="utf-8")
    for phrase in [
        "Operator:",
        "Commands Run",
        "Artifacts Generated",
        "Source Health",
        "Radar Output Quality",
        "Durable Artifact Status",
        "Final Status",
    ]:
        assert phrase in text
