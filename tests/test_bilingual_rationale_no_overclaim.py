from __future__ import annotations

from lattice_digest.recommendation_rationale import build_bilingual_rationale, format_bilingual_rationale_markdown


def test_title_only_paper_does_not_receive_invented_core_novelty() -> None:
    rationale = build_bilingual_rationale({"title": "A note on lattice signatures"})
    markdown = "\n".join(format_bilingual_rationale_markdown(rationale))

    assert rationale.confidence == "title_only"
    assert "证据不足，暂不能确认" in rationale.zh_core_novelty
    assert "Insufficient evidence" in rationale.en_core_novelty
    assert "method and contribution are not established" in rationale.en_paper_work_summary
    assert "TODO_VERIFY" in markdown


def test_missing_conclusion_does_not_produce_conclusion_claim_language() -> None:
    rationale = build_bilingual_rationale(
        {
            "title": "LWE estimator benchmark",
            "abstract": "We study LWE estimator benchmarks. We evaluate BKZ cost models for deployment.",
            "keywords_matched": ["LWE", "BKZ"],
        }
    )

    rendered = "\n".join(format_bilingual_rationale_markdown(rationale)).lower()
    assert rationale.confidence == "abstract_supported"
    assert "the conclusion says" not in rendered
    assert "the paper concludes" not in rendered
    assert "结论表明" not in rendered
    assert "摘要与结论证据" not in rendered


def test_weak_fhe_application_is_not_overpromoted_as_core() -> None:
    rationale = build_bilingual_rationale(
        {
            "title": "Private analytics over encrypted healthcare records",
            "abstract": (
                "We study healthcare analytics using homomorphic encryption and ciphertext packing. "
                "The system targets gradient boosting workflows and secure computation."
            ),
            "keywords_matched": ["FHE", "homomorphic encryption"],
        }
    )

    assert "peripheral" in rationale.en_radar_relevance
    assert "核心格攻击" in rationale.zh_radar_relevance
    assert not rationale.zh_recommendation.startswith("精读")
    assert not rationale.en_recommendation.startswith("Deep read")
