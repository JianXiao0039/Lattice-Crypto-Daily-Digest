from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.models import make_paper_record
from lattice_digest.radar_freshness import enrich_record_for_daily_radar
from lattice_digest.storage import write_json


def _paper(**overrides: object):
    data = {
        "title": "Module-SIS chameleon hash commitments from lattices",
        "abstract": "We construct lattice commitments from Module-SIS and discuss trapdoor adaptation.",
        "source": "iacr_eprint",
        "source_url": "https://eprint.iacr.org/2607/010",
        "publication_date": "2026-07-01",
        "relevance_label": "A",
        "relevance_score": 92,
    }
    data.update(overrides)
    return make_paper_record(**data)


def test_enriched_record_requires_bilingual_abstract_conclusion_and_recommendation_fields() -> None:
    enriched = enrich_record_for_daily_radar(_paper(), date(2026, 7, 1))

    assert enriched.title_en == "Module-SIS chameleon hash commitments from lattices"
    assert enriched.title_zh
    assert enriched.abstract_en.startswith("We construct")
    assert enriched.abstract_zh.startswith("model-generated zh summary:")
    assert enriched.conclusion_en.startswith("model-generated from available metadata:")
    assert enriched.conclusion_zh.startswith("model-generated zh summary:")
    assert enriched.recommendation_level == "Strong"
    assert enriched.recommendation_score >= 85
    assert "Module-SIS" in enriched.recommendation_reason
    assert "SIS/Module-SIS" in enriched.user_relevance_tags
    assert enriched.suggested_action == "Read today"


def test_missing_abstract_and_conclusion_use_todo_verify_markers() -> None:
    enriched = enrich_record_for_daily_radar(_paper(abstract=""), date(2026, 7, 1))

    assert enriched.abstract_en == "TODO_VERIFY"
    assert enriched.abstract_zh.startswith("TODO_VERIFY:")
    assert enriched.conclusion_en == "TODO_VERIFY"
    assert enriched.conclusion_zh.startswith("TODO_VERIFY:")
    assert {"abstract_en", "conclusion_en"} <= set(enriched.TODO_VERIFY_flags)


def test_json_output_contains_required_bilingual_and_recommendation_metadata() -> None:
    with TemporaryDirectory() as tmp:
        path = write_json([_paper()], Path(tmp), date(2026, 7, 1))
        item = json.loads(path.read_text(encoding="utf-8"))["records"][0]

    for field in (
        "title_en",
        "title_zh",
        "abstract_en",
        "abstract_zh",
        "conclusion_en",
        "conclusion_zh",
        "recommendation_level",
        "recommendation_score",
        "recommendation_reason",
        "TODO_VERIFY_flags",
        "source_urls",
        "evidence_tier",
        "source_health",
        "user_relevance_tags",
        "phd_application_relevance",
        "recommendation_risk_flags",
        "recommendation_evidence_basis",
        "recommendation_score_breakdown",
        "research_value_score",
        "primary_action_allowed",
        "suggested_action",
    ):
        assert field in item
    assert item["abstract_zh"].startswith("model-generated zh summary:")
    assert item["recommendation_level"] == "Strong"
