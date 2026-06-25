from __future__ import annotations

from lattice_digest.pqc_radar import ACADEMIC_SOURCES, OFFICIAL_STATUS_SOURCES, generate_query_templates, query_families


def test_minimal_source_aware_query_families_are_defined() -> None:
    families = query_families()

    assert set(families) == {
        "scheme_standardization",
        "hawk_high_precision",
        "scheme_migration",
        "scheme_protocol_pki",
        "scheme_implementation_security",
        "scheme_cryptanalysis",
    }

    for family in families.values():
        assert family.scheme_or_lattice_anchors
        assert family.process_or_event_anchors
        assert family.context_anchors
        assert family.production_retrieval_enabled is False


def test_academic_sources_are_distinct_from_official_status_sources() -> None:
    assert set(ACADEMIC_SOURCES) == {
        "arxiv",
        "iacr_eprint",
        "crossref",
        "dblp",
        "openalex",
        "semantic_scholar",
    }
    assert "nist_csrc" in OFFICIAL_STATUS_SOURCES
    assert "nist_csrc" not in ACADEMIC_SOURCES


def test_query_templates_use_required_boolean_architecture() -> None:
    templates = generate_query_templates()

    assert len(templates) == 6
    for template in templates:
        assert (
            template["architecture"]
            == "SCHEME_OR_LATTICE_ANCHOR AND PROCESS_OR_EVENT_ANCHOR AND CONTEXT_ANCHOR AND NOT NOISE_CONTEXT"
        )
        assert template["production_retrieval_enabled"] is False
        assert template["academic_sources"]


def test_hawk_query_family_contains_crypto_context_and_noise_terms() -> None:
    hawk = query_families()["hawk_high_precision"]

    assert "signature" in hawk.context_anchors
    assert "nist" in {item.lower() for item in hawk.context_anchors}
    assert "radar" in hawk.noise_terms
    assert "sports" in hawk.noise_terms
