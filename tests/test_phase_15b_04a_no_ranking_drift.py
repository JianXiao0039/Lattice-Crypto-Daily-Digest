from __future__ import annotations

from lattice_digest.models import make_paper_record
from lattice_digest.pqc_radar import classify_hawk_context
from lattice_digest.ranker import classify_record, infer_label, rank_paper


def test_existing_relevance_thresholds_are_unchanged() -> None:
    assert infer_label(80) == ("A", "必读")
    assert infer_label(60) == ("B", "值得跟踪")
    assert infer_label(40) == ("C", "可选关注")
    assert infer_label(39) == ("D", "过滤")


def test_generic_negative_keyword_semantics_are_unchanged() -> None:
    result = rank_paper(
        title="Crystal lattice thermal conductivity",
        abstract="A physics paper about phonon lattice vibration.",
        source="fixture",
        url="https://example.test/crystal-lattice",
    )

    assert result.label == "D"
    assert result.score == 0
    assert "crystal lattice" in result.negative_keywords


def test_existing_reading_priority_mapping_is_unchanged() -> None:
    record = make_paper_record(
        title="ML-KEM implementation benchmark",
        abstract="A lattice-based KEM implementation with constant-time NTT.",
        source="fixture",
        source_url="https://example.test/ml-kem",
    )
    ranked = classify_record(record, {}, {}, {})

    assert ranked.relevance_label in {"A", "B", "C", "D"}
    assert ranked.reading_priority in {1, 2, 3, 99}


def test_hawk_disambiguation_is_not_wired_into_generic_ranker_yet() -> None:
    hawk_decision = classify_hawk_context("Hawk radar system", "Defense radar upgrade.")
    ranker_result = rank_paper(
        title="Hawk radar system",
        abstract="Defense radar upgrade.",
        source="fixture",
        url="https://example.test/hawk-radar",
    )

    assert hawk_decision.accepted is False
    assert ranker_result.label == "D"
