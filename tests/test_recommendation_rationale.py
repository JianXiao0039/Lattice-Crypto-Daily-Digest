from __future__ import annotations

import py_compile
from pathlib import Path

from lattice_digest.recommendation_rationale import build_recommendation_rationale, rationale_to_dict


ROOT = Path(__file__).resolve().parents[1]


def test_abstract_rich_lwe_pqc_paper_produces_structured_rationale() -> None:
    rationale = build_recommendation_rationale(
        {
            "title": "Hybrid attacks against MLWE-based ML-KEM parameters",
            "abstract": (
                "We study the problem of estimating the security of MLWE instances used in ML-KEM. "
                "We propose a hybrid attack model that combines lattice reduction, coordinate guessing, and BKZ cost calibration. "
                "Our results improve the explanation of parameter margins for post-quantum deployment."
            ),
            "keywords_matched": ["MLWE", "ML-KEM", "BKZ"],
            "source": "iacr_eprint",
        }
    )

    assert rationale.confidence == "abstract_supported"
    assert "abstract-derived" in rationale.evidence_basis
    assert "MLWE" in rationale.radar_relevance or "mlwe" in rationale.radar_relevance.lower()
    assert "We propose a hybrid attack model" in rationale.method_summary
    assert "improve" in rationale.contribution_summary.lower()
    assert "精读" in rationale.recommendation_reason


def test_title_only_record_is_marked_title_only_without_fake_details() -> None:
    rationale = build_recommendation_rationale(
        {
            "title": "A note on lattice signatures",
        }
    )

    assert rationale.confidence == "title_only"
    assert rationale.evidence_basis == ["title-derived"]
    assert "不能可靠判断具体方法" in rationale.method_summary
    assert "不能可靠判断论文声称的新贡献" in rationale.contribution_summary
    assert "TODO_VERIFY" in rationale.caveat


def test_keyword_only_match_does_not_become_complete_rationale() -> None:
    rationale = build_recommendation_rationale(
        {
            "title": "Secure protocol overview",
            "keywords_matched": ["LWE", "signature"],
            "source": "openalex",
            "reason_for_priority": "Matched keywords: LWE, lattice, signature.",
        }
    )

    assert rationale.confidence == "repository_note_supported"
    assert "不能可靠判断具体方法" in rationale.method_summary
    assert "不能可靠判断论文声称的新贡献" in rationale.contribution_summary
    assert "关键词命中不能替代摘要" in rationale.caveat or "TODO_VERIFY" in rationale.caveat


def test_conclusion_is_used_only_when_present() -> None:
    no_conclusion = build_recommendation_rationale(
        {
            "title": "LWE estimator benchmark",
            "abstract": "We study LWE estimator benchmarks. We evaluate BKZ cost models for deployment.",
            "keywords_matched": ["LWE", "BKZ"],
        }
    )
    with_conclusion = build_recommendation_rationale(
        {
            "title": "LWE estimator benchmark",
            "abstract": "We study LWE estimator benchmarks. We evaluate BKZ cost models for deployment.",
            "conclusion": "Our results show that calibrated cost models change several deployment margins.",
            "keywords_matched": ["LWE", "BKZ"],
        }
    )

    assert "conclusion-derived" not in no_conclusion.evidence_basis
    assert no_conclusion.confidence == "abstract_supported"
    assert "conclusion-derived" in with_conclusion.evidence_basis
    assert with_conclusion.confidence == "conclusion_supported"
    assert "calibrated cost models" in with_conclusion.contribution_summary


def test_missing_full_paper_text_creates_todo_verify_caveat() -> None:
    rationale = build_recommendation_rationale(
        {
            "title": "Module-SIS commitments",
            "abstract": "We propose a commitment construction from Module-SIS.",
            "keywords_matched": ["Module-SIS", "commitment"],
        }
    )

    assert any(item.startswith("TODO_VERIFY") for item in rationale.todo_verify)
    assert "未见结论或全文" in rationale.caveat


def test_weak_fhe_application_is_marked_peripheral_not_core() -> None:
    rationale = build_recommendation_rationale(
        {
            "title": "Practical anonymous two-party gradient boosting decision tree",
            "abstract": (
                "We study anonymous GBDT training on split data for analytics. "
                "The system uses homomorphic encryption and ciphertext packing from ring learning with errors. "
                "Comparative experiments show the protocol remains competitive with leaky approaches."
            ),
            "keywords_matched": ["homomorphic encryption", "Learning with Errors"],
        }
    )

    assert "peripheral/temporary track" in rationale.radar_relevance
    assert rationale.recommendation_reason.startswith("暂存")
    assert "核心格攻击" in rationale.radar_relevance


def test_no_manual_annotation_fields_are_required() -> None:
    payload = rationale_to_dict(
        {
            "title": "ML-DSA implementation audit",
            "abstract": "We analyze implementation risks in ML-DSA deployments.",
            "keywords_matched": ["ML-DSA", "implementation"],
        }
    )

    assert "human_gold_label" not in payload
    assert "human_review_status" not in payload
    assert payload["confidence"] == "abstract_supported"


def test_python311_compatibility_is_preserved() -> None:
    py_compile.compile(str(ROOT / "src" / "lattice_digest" / "recommendation_rationale.py"), doraise=True)
