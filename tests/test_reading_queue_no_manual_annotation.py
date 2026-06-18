from __future__ import annotations

from lattice_digest.reading_queue import import_queue


def test_reading_queue_adds_no_human_gold_or_annotation_fields() -> None:
    candidate = {
        "title": "Module-SIS commitments for lattice protocols",
        "abstract": "This paper studies Module-SIS commitments for lattice-based protocols.",
        "source": "iacr_eprint",
        "source_url": "https://example.test/paper",
        "publication_date": "2026-06-15",
        "relevance_label": "A",
        "relevance_score": 91,
        "research_sections": ["SIS / NTRU / Commitments / Chameleon Hash"],
    }

    state, _ = import_queue({"records": []}, [candidate], timestamp="2026-06-18T00:00:00+00:00")
    record = state["records"][0]

    forbidden = {"user_label", "human_gold_label", "user_confirmed", "user_corrected", "manual_annotation_status"}
    assert forbidden.isdisjoint(record)
    assert record["reading_status"] == "TODO_READ"
    assert "rationale_problem" in record


def test_reading_queue_reading_action_is_explanation_not_score_change() -> None:
    candidate = {
        "title": "LWE attack cost analysis",
        "abstract": "We analyze LWE attack costs and present a benchmark for lattice reduction.",
        "source": "arxiv",
        "source_url": "https://example.test/lwe",
        "publication_date": "2026-06-15",
        "relevance_label": "A",
        "relevance_score": 93,
        "reading_priority_score": 77,
        "research_sections": ["LWE / RLWE / MLWE", "Lattice Reduction / Attacks"],
    }

    state, _ = import_queue({"records": []}, [candidate], timestamp="2026-06-18T00:00:00+00:00")
    record = state["records"][0]

    assert record["reading_action"] == "精读"
    assert record["relevance_score"] == 93
    assert record["reading_priority_score"] == 77
