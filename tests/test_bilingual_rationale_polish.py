from __future__ import annotations

from lattice_digest.recommendation_rationale import build_bilingual_rationale, format_bilingual_rationale_markdown


def test_top_lwe_pqc_paper_receives_bilingual_rationale() -> None:
    rationale = build_bilingual_rationale(
        {
            "title": "Hybrid attacks against MLWE-based ML-KEM parameters",
            "abstract": (
                "We study MLWE instances used in ML-KEM. "
                "We propose a hybrid attack model combining lattice reduction and BKZ cost calibration. "
                "Our results improve parameter-margin analysis for post-quantum deployment."
            ),
            "keywords_matched": ["MLWE", "ML-KEM", "BKZ"],
            "relevance_label": "A",
            "reading_priority_score": 90,
        },
        top_paper=True,
    )

    markdown = "\n".join(format_bilingual_rationale_markdown(rationale))
    assert "中文：" in markdown
    assert "论文大致工作：" in markdown
    assert "核心创新点：" in markdown
    assert "与本雷达关系：" in markdown
    assert "建议：" in markdown
    assert "TODO_VERIFY：" in markdown
    assert "English:" in markdown
    assert "Paper work summary:" in markdown
    assert "Core novelty:" in markdown
    assert "Radar relevance:" in markdown
    assert "Recommendation:" in markdown
    assert "TODO_VERIFY:" in markdown
    assert rationale.bilingual_policy_applied == "top_paper_full_bilingual"


def test_no_manual_annotation_fields_are_required_for_bilingual_rationale() -> None:
    payload = build_bilingual_rationale(
        {
            "title": "ML-DSA implementation audit",
            "abstract": "We analyze implementation risks in ML-DSA deployments.",
            "keywords_matched": ["ML-DSA", "implementation"],
        }
    ).to_dict()

    serialized = repr(payload)
    assert "human_gold_label" not in serialized
    assert "user_confirmed" not in serialized
    assert "manual_annotation_status" not in serialized
