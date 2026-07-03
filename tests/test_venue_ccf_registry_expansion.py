from __future__ import annotations

from datetime import date

from lattice_digest.digest import generate_markdown
from lattice_digest.models import make_paper_record, record_to_dict
from lattice_digest.radar_freshness import apply_daily_freshness_policy, detect_venue_metadata, enrich_record_for_daily_radar
from lattice_digest.venue_registry import VENUE_REGISTRY


def _paper(**overrides: object):
    data = {
        "title": "Lattice PQC venue metadata paper",
        "abstract": "This paper studies lattice cryptography, LWE, and PQC implementation.",
        "source": "crossref",
        "source_url": "https://example.test/paper",
        "publication_date": "2026-07-03",
        "relevance_label": "A",
        "relevance_score": 90,
        "taxonomy_tags": ["lwe_sis_ntru_foundations"],
    }
    data.update(overrides)
    return make_paper_record(**data)


def test_registry_schema_exposes_conservative_evidence_fields() -> None:
    ccs = next(entry for entry in VENUE_REGISTRY if entry.canonical_venue_name == "ACM CCS")
    cybersecurity = next(entry for entry in VENUE_REGISTRY if entry.canonical_venue_name == "Cybersecurity")
    crossref = next(entry for entry in VENUE_REGISTRY if entry.canonical_venue_name == "Crossref")

    assert ccs.ccf_rank == "A"
    assert ccs.ccf_status == "trusted_local"
    assert ccs.ccf_evidence_status == "repo_policy"
    assert cybersecurity.ccf_rank == "TODO_VERIFY"
    assert cybersecurity.todo_verify_required is True
    assert crossref.applicability == "metadata_index"
    assert crossref.ccf_rank == "N/A"


def test_known_local_ccf_a_and_b_venues_resolve_only_from_trusted_local_entries() -> None:
    ccf_a = enrich_record_for_daily_radar(_paper(venue="IEEE S&P", source="dblp"), date(2026, 7, 3))
    ccf_b = enrich_record_for_daily_radar(_paper(venue="PKC", source="crossref"), date(2026, 7, 3))

    assert ccf_a.CCF_rank == "A"
    assert ccf_b.CCF_rank == "B"
    assert detect_venue_metadata(ccf_a).ccf_status == "trusted_local"
    assert detect_venue_metadata(ccf_b).ccf_status == "trusted_local"


def test_known_crypto_and_security_venues_without_trusted_rank_stay_unknown_or_todo_verify() -> None:
    pqcrypto = enrich_record_for_daily_radar(_paper(venue="PQCrypto", source="dblp"), date(2026, 7, 3))
    raid = enrich_record_for_daily_radar(_paper(venue="RAID", source="dblp"), date(2026, 7, 3))

    assert pqcrypto.venue_type == "conference"
    assert pqcrypto.CCF_rank == "unknown"
    assert "venue" in pqcrypto.TODO_VERIFY_flags
    assert raid.venue_type == "conference"
    assert raid.CCF_rank == "unknown"
    assert "venue" in raid.TODO_VERIFY_flags


def test_preprint_and_eprint_sources_remain_non_ccf_ranked_preprints() -> None:
    arxiv = enrich_record_for_daily_radar(_paper(venue="", source="arxiv"), date(2026, 7, 3))
    eprint = enrich_record_for_daily_radar(_paper(venue="", source="iacr_eprint"), date(2026, 7, 3))

    assert arxiv.venue_type == "preprint"
    assert arxiv.CCF_rank == "N/A"
    assert eprint.venue_type == "preprint"
    assert eprint.CCF_rank == "N/A"


def test_metadata_sources_do_not_fabricate_ccf_rank_without_local_venue_match() -> None:
    for source in ("crossref", "dblp", "openalex", "semantic_scholar"):
        item = enrich_record_for_daily_radar(_paper(venue="", source=source), date(2026, 7, 3))
        assert item.venue_type == "indexing source"
        assert item.CCF_rank == "N/A"

    unknown_crossref_venue = enrich_record_for_daily_radar(
        _paper(venue="Local Security Workshop", source="crossref"),
        date(2026, 7, 3),
    )
    assert unknown_crossref_venue.venue_type == "workshop"
    assert unknown_crossref_venue.CCF_rank == "unknown"
    assert "venue" in unknown_crossref_venue.TODO_VERIFY_flags


def test_security_journals_are_conservative_and_item_visible_todo_verify() -> None:
    for venue in (
        "Cybersecurity",
        "Computers & Security",
        "IEEE Transactions on Information Forensics and Security",
        "ACM Transactions on Privacy and Security",
        "Journal of Computer Security",
    ):
        item = enrich_record_for_daily_radar(_paper(venue=venue, source="crossref"), date(2026, 7, 3))
        assert item.venue_type == "journal"
        assert item.CCF_rank == "TODO_VERIFY"
        assert {"venue", "CCF_rank"} <= set(item.TODO_VERIFY_flags)


def test_json_and_markdown_show_todo_verify_for_uncertain_venue_metadata() -> None:
    item = enrich_record_for_daily_radar(_paper(venue="Cybersecurity", source="crossref"), date(2026, 7, 3))
    payload = record_to_dict(item)
    markdown = generate_markdown([item], date(2026, 7, 3), 0, [], [], "36h", {"target_date": "2026-07-03"})

    assert payload["CCF_rank"] == "TODO_VERIFY"
    assert "CCF_rank" in payload["TODO_VERIFY_flags"]
    assert "CCF_rank：TODO_VERIFY" in markdown
    assert "TODO_VERIFY_flags" in markdown


def test_generated_markers_freshness_and_ranking_remain_unchanged_by_registry() -> None:
    old_high_score = _paper(
        venue="ACM CCS",
        publication_date="2026-06-20",
        update_date="2026-06-20",
        relevance_score=100,
    )
    primary, routed = apply_daily_freshness_policy([old_high_score], date(2026, 7, 3))
    assert primary == []
    assert routed[0].freshness_bucket == "backfill"
    assert routed[0].primary_today_new_eligible is False
    assert routed[0].recommendation_level == "Backfill"
    assert routed[0].abstract_zh.startswith("model-generated zh summary:")
    assert routed[0].conclusion_zh.startswith("model-generated zh summary:")
