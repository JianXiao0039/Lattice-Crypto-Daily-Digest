from __future__ import annotations

from lattice_digest.reading_queue import import_queue


def test_reading_queue_includes_rationale_fields_for_abstract_supported_record() -> None:
    candidate = {
        "title": "ML-KEM implementation hardening",
        "abstract": (
            "This paper studies side-channel hardening for ML-KEM implementations. "
            "It proposes a constant-time implementation strategy and evaluates microcontroller overhead. "
            "The results improve deployment guidance."
        ),
        "source": "crossref",
        "source_url": "https://example.test/ml-kem",
        "publication_date": "2026-06-15",
        "relevance_label": "B",
        "relevance_score": 72,
        "research_sections": ["PQC Standards / ML-KEM / ML-DSA / Falcon", "Implementation / Systems"],
        "source_health_ref": "crossref",
    }

    state, _ = import_queue({"records": []}, [candidate], timestamp="2026-06-18T00:00:00+00:00")
    record = state["records"][0]

    assert record["reading_action"] in {"扫读", "暂存"}
    assert record["evidence_basis"] == ["abstract-derived", "metadata-derived"]
    assert "rationale_problem" in record
    assert "rationale_method" in record
    assert record["source_health_context"]["source_health_ref"] == "crossref"
    assert record["first_seen"] == "2026-06-15"
    assert record["last_seen"] == "2026-06-15"


def test_title_only_record_stays_low_confidence_and_temporary() -> None:
    candidate = {
        "title": "Lattice keyword collision",
        "source": "openalex",
        "source_url": "https://example.test/title-only",
        "publication_date": "2026-06-15",
        "relevance_label": "C",
        "relevance_score": 41,
        "research_sections": ["PQC Standards / ML-KEM / ML-DSA / Falcon"],
    }

    state, _ = import_queue({"records": []}, [candidate], timestamp="2026-06-18T00:00:00+00:00")
    record = state["records"][0]

    assert record["reading_action"] == "暂存"
    assert record["rationale_confidence"] in {"title_only", "metadata_supported"}
    assert "不能可靠判断具体方法" in record["rationale_method"]
