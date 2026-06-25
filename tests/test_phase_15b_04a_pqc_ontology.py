from __future__ import annotations

from lattice_digest.models import make_paper_record, record_to_dict
from lattice_digest.pqc_radar import (
    ONTOLOGY_GROUPS,
    apply_metadata_defaults,
    load_pqc_radar_config,
    metadata_defaults,
    scheme_registry,
)


def test_required_ontology_groups_are_structured() -> None:
    required = {
        "lattice_assumptions",
        "scheme_families",
        "standardized_schemes",
        "active_candidates",
        "historical_candidates",
        "standardization_processes",
        "migration_lifecycle_events",
        "protocols_and_pki",
        "libraries_and_vendors",
        "hardware_and_embedded_systems",
        "implementation_security",
        "cryptanalysis",
        "regulation_and_jurisdictions",
        "industry_sectors",
        "multilingual_aliases",
        "disambiguation_requirements",
        "negative_contexts",
    }

    assert required <= set(ONTOLOGY_GROUPS)


def test_scheme_registry_covers_required_lattice_entities() -> None:
    registry = scheme_registry()
    required = {
        "ML-KEM",
        "ML-DSA",
        "FN-DSA",
        "HAWK",
        "NTRU",
        "NTRU-HRSS",
        "NTRU Prime",
        "FrodoKEM",
        "Saber",
        "NewHope",
        "LWE",
        "RLWE",
        "MLWE",
        "SIS",
        "Module-SIS",
        "NTRU assumptions",
        "lattice isomorphism problem",
        "module lattice isomorphism problem",
    }

    assert required <= set(registry)
    assert "FIPS 206" in registry["FN-DSA"].aliases
    assert "MLIP" in registry["module lattice isomorphism problem"].aliases
    assert registry["NewHope"].historical is True
    assert registry["Saber"].lifecycle_status == "historical_candidate"
    assert registry["ML-KEM"].lifecycle_status == "standardized"


def test_config_file_matches_non_production_query_contract() -> None:
    config = load_pqc_radar_config()

    assert config["schema_version"] == 1
    assert config["production_retrieval_enabled"] is False
    assert len(config["query_families"]) == 6
    assert {item["id"] for item in config["query_families"]} == {
        "scheme_standardization",
        "hawk_high_precision",
        "scheme_migration",
        "scheme_protocol_pki",
        "scheme_implementation_security",
        "scheme_cryptanalysis",
    }


def test_old_paper_record_deserialization_remains_strict_and_supported() -> None:
    old_record = make_paper_record(
        title="LWE and BKZ test fixture",
        source="fixture",
        source_url="https://example.test/lwe-bkz",
    )
    payload = record_to_dict(old_record)
    enriched = apply_metadata_defaults(payload)

    assert "scheme" not in payload
    assert old_record.relevance_label == "D"
    assert set(metadata_defaults()) <= set(enriched)
    assert enriched["scheme"] == ""
    assert enriched["TODO_VERIFY"] == []
