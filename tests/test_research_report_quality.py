from __future__ import annotations

from datetime import date

from lattice_digest.config import load_config_bundle
from lattice_digest.digest import generate_markdown
from lattice_digest.models import make_paper_record
from lattice_digest.ranker import classify_record
from lattice_digest.report_quality import (
    anchor_evidence_text,
    false_positive_risk_text,
    semantic_scholar_advisory_text,
)
from lattice_digest.research_artifact_export import render_advisor_update
from lattice_digest.weekly_synthesis import render_markdown


def _a_level_record():
    return make_paper_record(
        title="On the Secrecy of the Encapsulation Coin in ML-KEM",
        abstract="We analyze ML-KEM and Kyber encapsulation coin secrecy in post-quantum cryptography.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2026/1117",
        relevance_label="A",
        relevance_score=100,
        taxonomy_tags=["pqc_schemes"],
        keywords_matched=["ML-KEM", "Kyber"],
    )


def _weekly_payload() -> dict:
    a_record = {
        "title": "On the Secrecy of the Encapsulation Coin in ML-KEM",
        "abstract": "ML-KEM and Kyber security analysis.",
        "source": "iacr_eprint",
        "source_url": "https://eprint.iacr.org/2026/1117",
        "seen_sources": ["iacr_eprint"],
        "seen_dates": ["2026-06-03"],
        "relevance_label": "A",
        "relevance_score": 100,
        "research_sections": ["PQC Standards / ML-KEM / ML-DSA / Falcon"],
        "report_buckets": ["High-Priority Papers"],
        "semantic_scholar_metadata": {
            "corpusId": 123,
            "externalIds": {"DOI": "10.0000/ml-kem"},
            "venue": "IACR ePrint",
            "year": 2026,
            "citationCount": 7,
            "influentialCitationCount": 1,
            "openAccessPdf": {"url": "https://eprint.iacr.org/2026/1117.pdf"},
        },
    }
    generic = {
        "title": "Practical Anonymous Two-Party Gradient Boosting Decision Tree",
        "abstract": "A privacy-preserving federated learning system for GBDT.",
        "source": "crossref",
        "source_url": "https://doi.org/10.0000/gbdt",
        "seen_sources": ["crossref"],
        "seen_dates": ["2026-06-03"],
        "relevance_label": "C",
        "relevance_score": 42,
        "research_sections": [],
        "report_buckets": [],
    }
    return {
        "week_id": "2026-W23",
        "from_date": "2026-06-01",
        "to_date": "2026-06-07",
        "coverage": {
            "expected_days": 7,
            "loaded_days": ["2026-06-03"],
            "missing_days": ["2026-06-01"],
            "total_records": 2,
            "unique_records": 2,
            "label_counts": {"A": 1, "C": 1},
        },
        "label_counts": {"A": 1, "C": 1},
        "sections": {
            "PQC Standards / ML-KEM / ML-DSA / Falcon": [a_record],
            "LWE / RLWE / MLWE": [],
            "SIS / NTRU / Commitments / Chameleon Hash": [],
            "BKZ / LLL / G6K / Lattice Reduction / Attacks": [],
            "AI-assisted Lattice Cryptanalysis": [],
            "Implementation / Side-channel / Systems": [],
        },
        "report_buckets": {"High-Priority Papers": [a_record]},
        "idea_bank_candidates": [],
        "paper_plan_candidates": [],
        "source_health_summary": {
            "available": True,
            "sources": ["iacr_eprint", "semantic_scholar"],
            "status_counts": {"green": 1, "red": 1},
            "records": [
                {"source": "iacr_eprint", "status": "green", "final_count": 1},
                {"source": "semantic_scholar", "status": "red", "error_type": "rate_limit"},
            ],
        },
    }


def test_daily_report_surfaces_a_level_anchor_evidence_and_caveats() -> None:
    markdown = generate_markdown(
        [_a_level_record()],
        date(2026, 6, 3),
        source_health=[
            {"source": "iacr_eprint", "status": "green", "final_count": 1},
            {"source": "semantic_scholar", "status": "red", "error_type": "rate_limit"},
        ],
    )

    assert "## 2. 高优先级论文" in markdown
    assert "On the Secrecy of the Encapsulation Coin in ML-KEM" in markdown
    assert "lattice/PQC anchor evidence" in markdown
    assert "ML-KEM/Kyber" in markdown
    assert "Source health caveat" in markdown
    assert "semantic_scholar" in markdown


def test_generic_non_lattice_item_is_not_overclaimed() -> None:
    record = {
        "title": "Practical Anonymous Two-Party Gradient Boosting Decision Tree",
        "abstract": "A privacy-preserving federated learning method for GBDT without lattice cryptography.",
    }

    assert "未发现明确 lattice/PQC anchor" in anchor_evidence_text(record)
    assert "generic privacy/FL/LLM" in false_positive_risk_text(record)


def test_semantic_scholar_metadata_is_advisory_only() -> None:
    record = _weekly_payload()["sections"]["PQC Standards / ML-KEM / ML-DSA / Falcon"][0]
    advisory = semantic_scholar_advisory_text(record)

    assert "citationCount=7" in advisory
    assert "CorpusId=123" in advisory
    assert "仅作 advisory context" in advisory
    assert "不覆盖 A/B/C ranking" in advisory


def test_weekly_report_has_top_a_level_and_source_health_caveat() -> None:
    markdown = render_markdown(_weekly_payload())

    assert "## Top A-level Papers" in markdown
    assert "Anchor evidence: ML-KEM/Kyber" in markdown
    assert "Semantic Scholar advisory" in markdown
    assert "citationCount=7" in markdown
    assert "Caveat:" in markdown
    assert "semantic_scholar" in markdown


def test_advisor_update_separates_facts_ranking_and_advisory_metadata() -> None:
    payload = _weekly_payload()
    records = payload["report_buckets"]["High-Priority Papers"]
    text = render_advisor_update(payload, records, date(2026, 6, 1), date(2026, 6, 7))

    assert "Manual Review Caveats" in text
    assert "Anchor evidence" in text
    assert "Semantic Scholar advisory" in text
    assert "does not override A/B/C relevance ranking" in text


def test_report_quality_helpers_do_not_change_ranking_thresholds() -> None:
    configs = load_config_bundle()
    record = _a_level_record()
    before = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    anchor_evidence_text(record)
    false_positive_risk_text(record)
    semantic_scholar_advisory_text(record)

    after = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])
    assert after.relevance_score == before.relevance_score
    assert after.relevance_label == before.relevance_label
