from __future__ import annotations

from lattice_digest.config import load_config_bundle
from lattice_digest.models import make_paper_record
from lattice_digest.ranker import classify_record


def test_ranker_labels_core_lattice_cryptanalysis_as_a() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="Improved LWE and NTRU Cryptanalysis with BKZ",
        abstract="We study post-quantum cryptanalysis of LWE, SIS and NTRU using BKZ lattice reduction.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.00002",
    )

    ranked = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert ranked.relevance_label == "A"
    assert "lwe" in {term.lower() for term in ranked.keywords_matched}
    assert "lattice_reduction_cryptanalysis" in ranked.taxonomy_tags
    assert ranked.reading_priority == 1


def test_ranker_rejects_lattice_without_crypto_context() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="A lattice model for phonon thermal conductivity",
        abstract="The crystal lattice dynamics explain thermal conductivity in a material.",
        source="crossref",
        source_url="https://doi.org/10.0000/materials",
    )

    ranked = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert ranked.relevance_label == "D"
    assert ranked.reading_priority == 99

