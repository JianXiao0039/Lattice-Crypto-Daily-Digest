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


def test_ranker_rejects_lattice_word_only_without_crypto_context() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="Fast sampling on a periodic lattice graph",
        abstract="We study a lattice structure for graph traversal without security applications.",
        source="openalex",
        source_url="https://openalex.org/W-lattice-graph",
    )

    ranked = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert ranked.relevance_label == "D"


def test_cs_lg_without_explicit_crypto_context_is_filtered() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="Transformers for generic modular arithmetic",
        abstract="We study algorithmic reasoning and modular addition in neural networks.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.00003",
        categories=["cs.LG"],
    )

    ranked = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert ranked.relevance_label == "D"
    assert "cs.LG" in record.categories


def test_core_lattice_crypto_samples_enter_a_or_b() -> None:
    configs = load_config_bundle()
    samples = [
        (
            "Constant-time ML-KEM implementation on RISC-V",
            "We optimize Kyber polynomial arithmetic and NTT for post-quantum cryptography.",
        ),
        (
            "Fault attack countermeasures for ML-DSA and Dilithium",
            "We analyze lattice-based digital signature implementations under fault injection.",
        ),
        (
            "Falcon signature verification with improved Gaussian sampling",
            "The work studies FN-DSA and NTRU lattice signatures.",
        ),
        (
            "Bootstrapping optimization for FHE",
            "We improve TFHE, CKKS, BFV and BGV homomorphic encryption parameters.",
        ),
        (
            "Learning with Errors and Short Integer Solution cryptanalysis",
            "We study LWE, SIS, NTRU and BKZ lattice reduction attacks.",
        ),
    ]

    for title, abstract in samples:
        record = make_paper_record(
            title=title,
            abstract=abstract,
            source="iacr_eprint",
            source_url=f"https://eprint.iacr.org/2600/{abs(hash(title)) % 10000}",
        )

        ranked = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

        assert ranked.relevance_label in {"A", "B"}, ranked.reason
        assert ranked.relevance_score >= 60


def test_short_integer_solution_with_lattice_signatures_enters_a_or_b() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="Module lattice signatures from the Short Integer Solution problem",
        abstract="We construct lattice-based signatures using Module-SIS over q-ary module lattices.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2600/123",
    )

    ranked = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert ranked.relevance_label in {"A", "B"}, ranked.reason
    assert "short integer solution" in {term.lower() for term in ranked.keywords_matched}


def test_lwe_rlwe_mlwe_strong_sample_enters_a() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="A new attack on LWE, Ring-LWE and Module-LWE",
        abstract="The paper gives cryptanalysis of LWE, RLWE and MLWE using lattice reduction.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.00004",
        categories=["cs.CR"],
    )

    ranked = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert ranked.relevance_label == "A"


def test_side_channel_requires_lattice_scheme_target() -> None:
    configs = load_config_bundle()
    generic = make_paper_record(
        title="A side-channel attack on cache replacement policies",
        abstract="We study timing attack behavior in a generic software system.",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.00005",
        categories=["cs.CR"],
    )
    targeted = make_paper_record(
        title="Side-channel attack on Kyber decapsulation",
        abstract="We analyze a power analysis attack against an ML-KEM implementation.",
        source="iacr_eprint",
        source_url="https://eprint.iacr.org/2600/124",
    )

    generic_ranked = classify_record(generic, configs["taxonomy"], configs["keywords"], configs["negative"])
    targeted_ranked = classify_record(targeted, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert generic_ranked.relevance_label == "D"
    assert targeted_ranked.relevance_label in {"A", "B"}


def test_ai_assisted_lattice_cryptanalysis_with_bkz_context_enters_b_or_c() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="Learning-guided heuristics for cryptanalytic search",
        abstract="We use neural lattice reduction ideas for BKZ cost models and lattice cryptanalysis.",
        source="semantic_scholar",
        source_url="https://www.semanticscholar.org/paper/ai-lattice",
        categories=["cs.LG"],
    )

    ranked = classify_record(record, configs["taxonomy"], configs["keywords"], configs["negative"])

    assert ranked.relevance_label in {"B", "C"}, ranked.reason


def test_unreliable_source_or_url_is_filtered() -> None:
    configs = load_config_bundle()
    missing_url = make_paper_record(
        title="LWE cryptanalysis with BKZ",
        abstract="A post-quantum lattice cryptanalysis paper.",
        source="arxiv",
        source_url="",
    )
    missing_source = make_paper_record(
        title="LWE cryptanalysis with BKZ",
        abstract="A post-quantum lattice cryptanalysis paper.",
        source="",
        source_url="https://arxiv.org/abs/2601.00006",
    )

    assert classify_record(missing_url, configs["taxonomy"], configs["keywords"], configs["negative"]).relevance_label == "D"
    assert classify_record(missing_source, configs["taxonomy"], configs["keywords"], configs["negative"]).relevance_label == "D"
