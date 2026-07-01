from __future__ import annotations

from datetime import date

from lattice_digest.models import make_paper_record
from lattice_digest.radar_freshness import detect_venue_metadata, enrich_record_for_daily_radar


def _paper(**overrides: object):
    data = {
        "title": "ML-KEM implementation security update",
        "abstract": "The paper studies lattice-based PQC implementation security.",
        "source": "iacr_eprint",
        "source_url": "https://eprint.iacr.org/2607/001",
        "publication_date": "2026-07-01",
        "relevance_label": "A",
        "relevance_score": 90,
    }
    data.update(overrides)
    return make_paper_record(**data)


def test_venue_detection_represents_expected_source_families() -> None:
    cases = [
        (_paper(venue="ACM CCS", source="crossref"), "conference"),
        (_paper(venue="Journal of Cryptology", source="crossref"), "journal"),
        (_paper(venue="arXiv", source="arxiv"), "preprint"),
        (_paper(venue="NIST PQC", source="nist"), "standardization body"),
        (_paper(venue="Vendor security advisory", source="vendor release"), "vendor/security advisory"),
        (_paper(venue="Unknown Workshop", source="unknown"), "workshop"),
        (_paper(venue="Unclassified Source", source="unknown"), "unknown"),
    ]

    for record, expected_type in cases:
        assert detect_venue_metadata(record).venue_type == expected_type


def test_ccf_rank_uses_known_local_metadata_or_safe_unknown_values() -> None:
    ccf_a = enrich_record_for_daily_radar(_paper(venue="ACM CCS", source="crossref"), date(2026, 7, 1))
    ccf_b = enrich_record_for_daily_radar(_paper(venue="PKC", source="crossref"), date(2026, 7, 1))
    preprint = enrich_record_for_daily_radar(_paper(venue="IACR ePrint", source="iacr_eprint"), date(2026, 7, 1))
    unknown = enrich_record_for_daily_radar(_paper(venue="Local Security Workshop", source="crossref"), date(2026, 7, 1))

    assert ccf_a.CCF_rank == "A"
    assert ccf_b.CCF_rank == "B"
    assert preprint.CCF_rank == "N/A"
    assert unknown.CCF_rank == "unknown"


def test_cybersecurity_journal_candidate_is_represented_as_todo_verify() -> None:
    record = enrich_record_for_daily_radar(
        _paper(venue="Cybersecurity", source="crossref"),
        date(2026, 7, 1),
    )

    assert record.venue_type == "journal"
    assert record.CCF_rank == "TODO_VERIFY"
    assert record.venue_status == "TODO_VERIFY"
    assert "venue" in record.TODO_VERIFY_flags
