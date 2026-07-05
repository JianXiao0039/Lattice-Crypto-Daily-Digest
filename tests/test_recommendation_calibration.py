from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.digest import generate_markdown, record_intelligence
from lattice_digest.models import make_paper_record
from lattice_digest.radar_freshness import apply_daily_freshness_policy, enrich_record_for_daily_radar
from lattice_digest.storage import write_json


def _paper(**overrides: object):
    data = {
        "title": "Sparse LWE cryptanalysis with BKZ cost models",
        "abstract": "We study sparse LWE cryptanalysis using BKZ, G6K and hybrid attacks.",
        "source": "arxiv",
        "source_url": "https://arxiv.org/abs/2607.00001",
        "venue": "arXiv",
        "publication_date": "2026-07-03",
        "relevance_label": "A",
        "relevance_score": 94,
    }
    data.update(overrides)
    return make_paper_record(**data)


def test_lattice_cryptanalysis_primary_item_becomes_strong_with_concrete_axes() -> None:
    item = enrich_record_for_daily_radar(_paper(), date(2026, 7, 3))

    assert item.recommendation_level == "Strong"
    assert item.recommendation_score >= 85
    assert {"Sparse LWE/RLWE/MLWE", "Lattice cryptanalysis", "Lattice reduction/BKZ/G6K"} <= set(
        item.user_relevance_tags
    )
    assert "Sparse LWE" in item.recommendation_reason
    assert item.primary_action_allowed is True
    assert item.suggested_action == "Read today"


def test_module_sis_and_mldsa_topics_get_high_user_relevance() -> None:
    module_sis = enrich_record_for_daily_radar(
        _paper(
            title="Module-SIS chameleon hash commitments from lattices",
            abstract="The construction uses Module-SIS commitments, trapdoor adaptation and chameleon hash.",
            source="iacr_eprint",
            source_url="https://eprint.iacr.org/2607/010",
            venue="IACR ePrint",
        ),
        date(2026, 7, 3),
    )
    mldsa = enrich_record_for_daily_radar(
        _paper(
            title="ML-DSA implementation security for Dilithium signatures",
            abstract="The paper studies ML-DSA, Dilithium and lattice signature implementation security.",
            source="dblp",
            source_url="https://dblp.org/rec/conf/example/mldsa",
            venue="ACM CCS",
        ),
        date(2026, 7, 3),
    )

    assert module_sis.recommendation_level == "Strong"
    assert {"SIS/Module-SIS", "Chameleon hash/trapdoor primitives"} <= set(module_sis.user_relevance_tags)
    assert mldsa.recommendation_level == "Strong"
    assert {"ML-DSA/Dilithium", "Lattice signatures"} <= set(mldsa.user_relevance_tags)


def test_generic_security_and_generic_ai_do_not_become_strong() -> None:
    security = enrich_record_for_daily_radar(
        _paper(
            title="Enterprise cybersecurity monitoring at ACM CCS",
            abstract="A general security operations paper about enterprise monitoring and incident triage.",
            source="dblp",
            venue="ACM CCS",
            relevance_score=98,
        ),
        date(2026, 7, 3),
    )
    ai = enrich_record_for_daily_radar(
        _paper(
            title="Transformer models for traffic forecasting",
            abstract="A generic AI model for time series forecasting and urban mobility prediction.",
            source="crossref",
            venue="Unknown Journal",
            relevance_score=90,
        ),
        date(2026, 7, 3),
    )

    assert security.recommendation_level == "TODO_VERIFY"
    assert "no_concrete_user_axis" in security.recommendation_risk_flags
    assert ai.recommendation_level == "TODO_VERIFY"
    assert "no_concrete_user_axis" in ai.recommendation_risk_flags


def test_fhe_application_is_medium_unless_directly_tied_to_core_attack_axis() -> None:
    fhe = enrich_record_for_daily_radar(
        _paper(
            title="Private analytics with CKKS homomorphic encryption",
            abstract="The paper uses CKKS and fully homomorphic encryption for healthcare inference.",
            relevance_score=92,
        ),
        date(2026, 7, 3),
    )

    assert fhe.recommendation_level == "Medium"
    assert "FHE/lattice HE" in fhe.user_relevance_tags
    assert "Lattice cryptanalysis" not in fhe.user_relevance_tags


def test_venue_confidence_cannot_override_weak_topic_but_weak_venue_strong_topic_keeps_risk_flags() -> None:
    strong_venue_weak_topic = enrich_record_for_daily_radar(
        _paper(
            title="Database access control for enterprise systems",
            abstract="A systems security paper about database policy enforcement and enterprise access control.",
            source="dblp",
            venue="IEEE S&P",
            relevance_score=99,
        ),
        date(2026, 7, 3),
    )
    weak_venue_strong_topic = enrich_record_for_daily_radar(
        _paper(
            title="Sparse LWE hybrid attack ranking",
            abstract="Sparse LWE cryptanalysis with BKZ and hybrid attack ranking.",
            source="crossref",
            venue="Unknown Security Workshop",
        ),
        date(2026, 7, 3),
    )

    assert strong_venue_weak_topic.recommendation_level != "Strong"
    assert weak_venue_strong_topic.recommendation_level == "Strong"
    assert "venue_todo_verify" in weak_venue_strong_topic.recommendation_risk_flags


def test_backfill_retains_research_value_but_never_primary_read_today_action() -> None:
    _, routed = apply_daily_freshness_policy(
        [_paper(publication_date="2026-06-20", relevance_score=100)],
        date(2026, 7, 3),
    )
    item = routed[0]
    intelligence = record_intelligence(item)

    assert item.freshness_bucket == "backfill"
    assert item.primary_today_new_eligible is False
    assert item.recommendation_level == "Backfill"
    assert item.research_value_score >= item.recommendation_score
    assert item.recommendation_score <= 79
    assert item.suggested_action != "Read today"
    assert intelligence["suggested_action"] != "Read today"


def test_missing_date_and_source_health_risks_are_visible() -> None:
    missing_date = enrich_record_for_daily_radar(_paper(publication_date=None), date(2026, 7, 3))
    red = enrich_record_for_daily_radar(_paper(source_health="red"), date(2026, 7, 3))
    yellow = enrich_record_for_daily_radar(_paper(source_health="yellow"), date(2026, 7, 3))

    assert missing_date.recommendation_level == "TODO_VERIFY"
    assert "missing_date_basis" in missing_date.recommendation_risk_flags
    assert red.recommendation_level == "TODO_VERIFY"
    assert "source_health_red" in red.recommendation_risk_flags
    assert "source_health_yellow" in yellow.recommendation_risk_flags


def test_json_serializes_calibrated_fields_and_generated_markers_remain_intact() -> None:
    with TemporaryDirectory() as tmp:
        path = write_json([_paper()], Path(tmp), date(2026, 7, 3))
        item = json.loads(path.read_text(encoding="utf-8"))["records"][0]

    for field in (
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
    assert item["conclusion_zh"].startswith("model-generated zh summary:")
    assert item["recommendation_reason"] != "important paper"


def test_markdown_renders_calibrated_recommendation_fields() -> None:
    markdown = generate_markdown([_paper()], date(2026, 7, 3))

    assert "user_relevance_tags：" in markdown
    assert "phd_application_relevance：" in markdown
    assert "recommendation_risk_flags：" in markdown
    assert "recommendation_evidence_basis：" in markdown
    assert "primary_action_allowed：True" in markdown
    assert "suggested_action：今日精读" in markdown


def test_venue_rules_and_scratch_schema_remain_unchanged() -> None:
    arxiv = enrich_record_for_daily_radar(_paper(source="arxiv", venue="arXiv"), date(2026, 7, 3))
    eprint = enrich_record_for_daily_radar(_paper(source="iacr_eprint", venue="IACR ePrint"), date(2026, 7, 3))
    crossref = enrich_record_for_daily_radar(_paper(source="crossref", venue="Unknown Venue"), date(2026, 7, 3))

    assert arxiv.venue_type == "preprint"
    assert arxiv.CCF_rank == "N/A"
    assert eprint.venue_type in {"ePrint", "preprint"}
    assert eprint.CCF_rank == "N/A"
    assert crossref.CCF_rank in {"unknown", "TODO_VERIFY"}
