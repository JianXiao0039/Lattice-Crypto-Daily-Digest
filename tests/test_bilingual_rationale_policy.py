from __future__ import annotations

from pathlib import Path

from lattice_digest.recommendation_rationale import build_recommendation_rationale
from scripts.verify_v0_5_rc import bilingual_policy_checks


def test_bilingual_policy_document_requires_top_paper_scope(tmp_path: Path) -> None:
    path = tmp_path / "docs/research_tracks/v0.5_rc_bilingual_rationale_policy_v0.1.md"
    path.parent.mkdir(parents=True)
    path.write_text("中文\nEnglish\nA-class\ntop weekly\ntop monthly\n", encoding="utf-8")

    result = bilingual_policy_checks(tmp_path)

    assert result["status"] == "bilingual_rationale_policy_ready"
    assert result["ok"] is True


def test_conclusion_is_used_only_when_present() -> None:
    with_conclusion = build_recommendation_rationale(
        {
            "title": "LWE paper",
            "abstract": "This paper studies Learning With Errors.",
            "conclusion": "We conclude with parameter guidance for ML-KEM.",
        }
    )
    without_conclusion = build_recommendation_rationale(
        {"title": "LWE paper", "abstract": "This paper studies Learning With Errors."}
    )

    assert with_conclusion.confidence == "conclusion_supported"
    assert "conclusion-derived" in with_conclusion.evidence_basis
    assert without_conclusion.confidence == "abstract_supported"
    assert "conclusion-derived" not in without_conclusion.evidence_basis


def test_title_only_record_does_not_hallucinate_core_innovation() -> None:
    rationale = build_recommendation_rationale({"title": "Lattice keyword only"})

    assert rationale.confidence == "title_only"
    assert "不能可靠判断" in rationale.method_summary
    assert "不能可靠判断" in rationale.contribution_summary
