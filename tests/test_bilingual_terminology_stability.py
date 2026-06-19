from __future__ import annotations

from lattice_digest.recommendation_rationale import TERMINOLOGY_TABLE, build_bilingual_rationale


def test_required_bilingual_terminology_is_stable() -> None:
    expected = {
        "LWE": "Learning With Errors（LWE）",
        "RLWE": "Ring-LWE（RLWE）",
        "MLWE": "Module-LWE（MLWE）",
        "SIS": "Short Integer Solution（SIS）",
        "Module-SIS": "Module-SIS",
        "BKZ": "BKZ",
        "ML-KEM": "ML-KEM",
        "ML-DSA": "ML-DSA",
        "FHE": "全同态加密（FHE）",
        "CKKS": "CKKS",
    }

    for key, value in expected.items():
        assert TERMINOLOGY_TABLE[key] == value


def test_awkward_literal_translations_are_not_emitted() -> None:
    rationale = build_bilingual_rationale(
        {
            "title": "Ring signatures from lattice commitments",
            "abstract": "We propose a ring signature construction from lattice commitments.",
            "keywords_matched": ["lattice", "ring signature", "commitment"],
        }
    )

    rendered = "\n".join(
        [
            rationale.zh_paper_work_summary,
            rationale.zh_core_novelty,
            rationale.zh_radar_relevance,
            rationale.zh_recommendation,
        ]
    )
    assert "格子密码" not in rendered
    assert "学习带错误" not in rendered
    assert "戒指签名" not in rendered
    assert rationale.terminology_warnings == []
