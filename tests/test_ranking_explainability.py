from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.digest import generate_markdown
from lattice_digest.models import make_paper_record
from lattice_digest.ranker import rank_record, rank_records
from lattice_digest.ranking_explainability import build_ranking_explanation, concise_ranking_explanation
from lattice_digest.storage import write_json


def _taxonomy_config() -> dict[str, object]:
    return {
        "research": {
            "A01_lattice_reduction": {"keywords": ["BKZ", "lattice reduction"]},
            "H01_ai_lattice": {"keywords": ["AI-assisted lattice cryptanalysis"]},
        }
    }


def test_ranking_explanation_is_attached_to_ranked_records() -> None:
    record = make_paper_record(
        title="AI-assisted lattice cryptanalysis for LWE with BKZ",
        abstract="We study AI-assisted lattice cryptanalysis and lattice reduction for LWE attacks.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.90001",
    )
    ranked = rank_records([record], _taxonomy_config(), {}, {})[0]

    explanation = build_ranking_explanation(ranked)

    assert explanation["schema_version"] == 1
    assert explanation["relevance_score"] == ranked.relevance_score
    assert explanation["relevance_label"] == ranked.relevance_label
    assert explanation["decision"] == "include"
    assert explanation["positive_signals"]


def test_ranking_explanation_does_not_change_score_or_label() -> None:
    record = make_paper_record(
        title="BKZ cost models for LWE primal attacks",
        abstract="LWE, BKZ, lattice reduction, primal attack and hybrid attack.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2601/001",
    )
    before = rank_record(record)
    ranked = rank_records([record], {}, {}, {})[0]

    _ = build_ranking_explanation(ranked)
    after = rank_record(record)

    assert before.score == after.score
    assert before.label == after.label
    assert ranked.relevance_score == before.score
    assert ranked.relevance_label == before.label


def test_positive_keyword_and_taxonomy_matches_are_recorded() -> None:
    record = make_paper_record(
        title="AI-assisted lattice cryptanalysis for LWE with BKZ",
        abstract="The paper studies AI-assisted lattice cryptanalysis for LWE and BKZ.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.90002",
    )
    ranked = rank_records([record], _taxonomy_config(), {}, {})[0]
    explanation = build_ranking_explanation(ranked)
    keyword_signal = next(item for item in explanation["positive_signals"] if item["signal"] == "keyword_matches")
    taxonomy_signal = next(item for item in explanation["positive_signals"] if item["signal"] == "taxonomy_matches")

    assert "lwe" in [term.lower() for term in keyword_signal["matches"]]
    assert "A01_lattice_reduction" in taxonomy_signal["matches"]
    assert "H01_ai_lattice" in taxonomy_signal["matches"]
    assert keyword_signal["score_delta"] is None


def test_negative_keyword_matches_are_recorded() -> None:
    record = make_paper_record(
        title="Crystal lattice cryptography for LWE attacks",
        abstract="This intentionally mixed example mentions crystal lattice and LWE cryptanalysis.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.90003",
    )
    ranked = rank_records([record], {}, {}, {})[0]
    explanation = build_ranking_explanation(ranked)
    negative_signal = next(item for item in explanation["negative_signals"] if item["signal"] == "negative_keyword_matches")

    assert "crystal lattice" in negative_signal["matches"]
    assert negative_signal["score_delta"] is None


def test_json_output_contains_ranking_explanation() -> None:
    record = make_paper_record(
        title="Improved MLWE estimates for ML-KEM",
        abstract="We analyze MLWE and Kyber security estimates.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.90004",
        relevance_label="A",
        relevance_score=90,
        keywords_matched=["MLWE", "Kyber"],
        taxonomy_tags=["pqc_lattice_schemes"],
    )

    with TemporaryDirectory() as tmp:
        path = write_json([record], Path(tmp), date(2026, 5, 31))
        payload = json.loads(path.read_text(encoding="utf-8"))

    explanation = payload["records"][0]["ranking_explanation"]
    assert explanation["relevance_score"] == 90
    assert explanation["relevance_label"] == "A"
    assert explanation["matched_taxonomy"] == ["pqc_lattice_schemes"]


def test_markdown_output_contains_concise_ranking_explanation() -> None:
    record = make_paper_record(
        title="Transformer LWE hybrid attack ranking",
        abstract="AI-assisted lattice cryptanalysis for LWE with BKZ.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.90005",
        relevance_label="A",
        relevance_score=88,
        keywords_matched=["LWE", "BKZ", "AI-assisted lattice cryptanalysis"],
    )

    markdown = generate_markdown([record], date(2026, 5, 31))

    assert "Ranking: A / 88" in markdown
    assert "matched AI-assisted lattice cryptanalysis, BKZ, LWE" in markdown
    assert "no negative signals" in markdown


def test_explanation_ordering_is_deterministic() -> None:
    record = make_paper_record(
        title="LWE and BKZ",
        abstract="AI-assisted lattice cryptanalysis.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.90006",
        relevance_label="A",
        relevance_score=85,
        keywords_matched=["LWE", "AI-assisted lattice cryptanalysis", "BKZ", "LWE"],
        taxonomy_tags=["z_tag", "a_tag", "z_tag"],
        negative_keywords_matched=["lattice qcd", "crystal lattice"],
    )

    first = build_ranking_explanation(record)
    second = build_ranking_explanation(record)

    assert first == second
    assert first["positive_signals"][0]["matches"] == ["AI-assisted lattice cryptanalysis", "BKZ", "LWE"]
    assert first["matched_taxonomy"] == ["a_tag", "z_tag"]
    assert first["negative_signals"][0]["matches"] == ["crystal lattice", "lattice qcd"]
    assert concise_ranking_explanation(record) == concise_ranking_explanation(record)
