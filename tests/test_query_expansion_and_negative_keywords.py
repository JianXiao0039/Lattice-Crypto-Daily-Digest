from __future__ import annotations

from pathlib import Path

from lattice_digest.config import load_config_bundle
from lattice_digest.filters import negative_matches, should_exclude_as_negative
from lattice_digest.models import make_paper_record


ROOT = Path(__file__).resolve().parents[1]


def _sources_by_name() -> dict[str, dict]:
    configs = load_config_bundle()
    return {source["name"]: source for source in configs["sources"]["sources"]}


def _all_query_strings() -> list[str]:
    sources = _sources_by_name()
    queries: list[str] = []
    for source in sources.values():
        queries.extend(source.get("query_terms", []))
        queries.extend(source.get("queries", []))
        for group in source.get("query_groups", []):
            queries.append(" ".join(group))
    return queries


def _lower_queries() -> set[str]:
    return {query.lower() for query in _all_query_strings()}


def _negative_terms() -> set[str]:
    configs = load_config_bundle()
    negative = configs["negative"]
    terms: set[str] = set()
    for group in negative.get("hard_negative", {}).values():
        terms.update(term.lower() for term in group)
    terms.update(term.lower() for term in negative.get("soft_negative", []))
    return terms


def test_lattice_privacy_fl_llm_queries_are_anchored() -> None:
    queries = _lower_queries()

    for query in [
        "lattice-based secure aggregation federated learning",
        "rlwe-based secure aggregation federated learning",
        "lwe-based secure aggregation federated learning",
        "homomorphic encryption private federated learning rlwe",
        "fhe private llm fine-tuning rlwe",
        "post-quantum secure aggregation federated learning",
        "lattice-based privacy-preserving training",
        "rlwe encrypted gradient aggregation",
    ]:
        assert query in queries


def test_generic_privacy_fl_llm_queries_are_not_standalone() -> None:
    queries = _lower_queries()

    for generic_query in [
        "federated learning",
        "llm fine-tuning",
        "dp-sgd",
        "private training",
        "secure aggregation",
    ]:
        assert generic_query not in queries


def test_registration_based_encryption_queries_are_lattice_or_pqc_anchored() -> None:
    queries = _lower_queries()

    for query in [
        "lattice-based registration-based encryption",
        "lwe-based registration-based encryption",
        "sis-based registration-based encryption",
        "post-quantum registration-based encryption",
        "pqc registration-based encryption",
        "registration-based encryption from lattices",
    ]:
        assert query in queries

    for generic_query in [
        "registration encryption",
        "user registration encryption",
        "account registration",
        "registered user encryption",
    ]:
        assert generic_query not in queries


def test_lattice_isomorphism_queries_and_generic_isomorphism_negatives() -> None:
    queries = _lower_queries()
    negatives = _negative_terms()

    for query in [
        "lattice isomorphism problem",
        "isomorphism of lattices",
        "lattice automorphism cryptography",
        "lattice isomorphism post-quantum",
        "structured lattice isomorphism",
    ]:
        assert query in queries

    for negative in [
        "graph isomorphism",
        "code isomorphism",
        "model isomorphism",
        "neural isomorphism",
        "chemical isomorphism",
        "image registration",
        "point cloud registration",
    ]:
        assert negative in negatives
        assert negative not in queries


def test_advanced_lattice_primitive_queries_are_anchored() -> None:
    queries = _lower_queries()

    for query in [
        "module-sis chameleon hash",
        "sis-based commitment",
        "lattice-based commitment",
        "lattice-based anonymous credential",
        "lattice-based ring signature",
        "lwe-based functional encryption",
        "lattice-based zero-knowledge proof",
        "pqc attribute-based encryption",
    ]:
        assert query in queries

    for generic_query in [
        "zero-knowledge proof",
        "anonymous credential",
        "commitment scheme",
        "functional encryption",
        "attribute-based encryption",
    ]:
        assert generic_query not in queries


def test_obvious_registration_and_isomorphism_false_positives_are_suppressed() -> None:
    configs = load_config_bundle()

    false_positives = [
        make_paper_record(
            title="Medical image registration with compressed storage",
            abstract="An image registration pipeline for clinical data alignment.",
            source="openalex",
            source_url="https://example.test/image-registration",
        ),
        make_paper_record(
            title="Graph isomorphism for neural architecture matching",
            abstract="We study graph isomorphism and model isomorphism in machine learning.",
            source="openalex",
            source_url="https://example.test/graph-isomorphism",
        ),
        make_paper_record(
            title="Domain registration system with account registration",
            abstract="A web registration system for users and certificates.",
            source="openalex",
            source_url="https://example.test/domain-registration",
        ),
    ]

    for record in false_positives:
        excluded, matches = should_exclude_as_negative(record, configs["keywords"], configs["negative"])
        assert excluded is True
        assert matches


def test_lattice_pqc_anchored_true_positives_are_not_suppressed() -> None:
    configs = load_config_bundle()

    true_positives = [
        make_paper_record(
            title="LWE-based registration-based encryption",
            abstract="A post-quantum registration-based encryption construction from lattices.",
            source="iacr_eprint",
            source_url="https://eprint.iacr.org/2600/100",
        ),
        make_paper_record(
            title="RLWE-based secure aggregation for federated learning",
            abstract="We use homomorphic encryption over RLWE to aggregate encrypted gradients.",
            source="arxiv",
            source_url="https://arxiv.org/abs/2601.00001",
        ),
        make_paper_record(
            title="Lattice-based zero-knowledge proof for anonymous credentials",
            abstract="The construction relies on Module-SIS commitments and post-quantum assumptions.",
            source="iacr_eprint",
            source_url="https://eprint.iacr.org/2600/101",
        ),
    ]

    for record in true_positives:
        excluded, matches = should_exclude_as_negative(record, configs["keywords"], configs["negative"])
        assert excluded is False
        assert isinstance(matches, list)


def test_generic_privacy_terms_are_recorded_as_soft_negative_context() -> None:
    configs = load_config_bundle()
    record = make_paper_record(
        title="DP-SGD for generic LLM fine-tuning",
        abstract="We study private training and federated learning without cryptographic assumptions.",
        source="openalex",
        source_url="https://example.test/generic-dp-sgd",
    )

    excluded, matches = should_exclude_as_negative(record, configs["keywords"], configs["negative"])
    all_matches = negative_matches(record, configs["negative"])

    assert excluded is False
    assert {"DP-SGD", "federated learning", "LLM fine-tuning", "private training"} <= set(all_matches)
    assert set(matches) <= set(all_matches)


def test_query_order_is_deterministic_and_deduplicated() -> None:
    sources = _sources_by_name()
    arxiv = sources["arxiv"]

    assert arxiv["query_terms"] == list(dict.fromkeys(arxiv["query_terms"]))
    group_keys = [" ".join(group) for group in arxiv["query_groups"]]
    assert group_keys == list(dict.fromkeys(group_keys))
    assert group_keys[:10] == [
        "lattice cryptography",
        "Learning with Errors",
        "Ring-LWE RLWE",
        "Module-LWE MLWE",
        "SIS Short Integer Solution",
        "Kyber ML-KEM",
        "Dilithium ML-DSA",
        "BKZ lattice reduction",
        "neural lattice reduction",
        "Transformer LWE",
    ]


def test_no_scheduled_automation_files_are_added() -> None:
    forbidden_paths = [
        "watcher.ps1",
        "start_watcher.bat",
        "install_watcher_task.ps1",
        "uninstall_watcher_task.ps1",
        "scripts/watcher.ps1",
        "scripts/start_watcher.bat",
        "scripts/install_watcher_task.ps1",
        "scripts/uninstall_watcher_task.ps1",
    ]

    for relative_path in forbidden_paths:
        assert not (ROOT / relative_path).exists()
