from __future__ import annotations

from lattice_digest.config import load_config_bundle
from lattice_digest.filters import should_exclude_as_negative
from lattice_digest.models import make_paper_record


def test_negative_filter_excludes_materials_lattice_without_crypto() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="Optical lattice effects in condensed matter",
        abstract="We study spin lattice defects and lattice thermal conductivity.",
        source="openalex",
        source_url="https://openalex.org/W-materials",
    )

    excluded, matches = should_exclude_as_negative(record, configs["keywords"], configs["negative"])

    assert excluded is True
    assert "optical lattice" in matches
    assert "lattice thermal conductivity" in matches


def test_negative_filter_keeps_crypto_context_for_review() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="Constant-time implementation of a lattice-based KEM",
        abstract="We discuss side-channel resistance for post-quantum cryptography implementations.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2600/001",
    )

    excluded, matches = should_exclude_as_negative(record, configs["keywords"], configs["negative"])

    assert excluded is False
    assert matches == []


def test_non_crypto_sis_model_is_not_lattice_crypto() -> None:
    from lattice_digest.ranker import classify_record

    configs = load_config_bundle()
    record = make_paper_record(
        title="Effect of diffusion rates on a nonlocal SIS model with distinct dispersal kernels",
        abstract="A susceptible infectious model with a logistic source.",
        source="crossref",
        source_url="https://doi.org/10.0000/noncrypto-sis",
    )

    ranked = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert ranked.relevance_label == "D"
    assert "sis" in {term.lower() for term in ranked.keywords_matched}
