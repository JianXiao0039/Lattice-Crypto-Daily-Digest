from __future__ import annotations

from lattice_digest.config import load_config_bundle
from lattice_digest.pqc_radar import map_existing_taxonomy_keywords


def test_all_existing_taxonomy_keywords_are_accounted_for() -> None:
    mapping = map_existing_taxonomy_keywords()

    assert len(mapping) == 448
    assert all(row["retained"] is True for row in mapping)
    assert all(row["deprecation_status"] == "retained" for row in mapping)
    assert not [row for row in mapping if row["conflict"]]


def test_all_existing_taxonomy_categories_are_mapped() -> None:
    mapping = map_existing_taxonomy_keywords()
    categories = {row["original_category"] for row in mapping}

    assert len(categories) == 31
    assert all(row["new_ontology_group"] for row in mapping)


def test_existing_config_files_remain_backward_compatible() -> None:
    bundle = load_config_bundle()

    assert set(bundle) == {"taxonomy", "keywords", "negative", "sources"}
    assert "A_algorithms_and_attacks" in bundle["taxonomy"]
    assert "C_standard_lattice_pqc" in bundle["taxonomy"]
    assert "hard_negative" in bundle["negative"]
    assert "sources" in bundle["sources"]
