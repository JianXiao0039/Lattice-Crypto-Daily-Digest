from __future__ import annotations

from lattice_digest.digest_sections import (
    GENERAL_CRYPTO_PRIVACY,
    LATTICE_ADVANCED_PRIMITIVES,
    LATTICE_ISOMORPHISM,
    LATTICE_PRIVACY_FL,
    LWE_FAMILY,
    REGISTRATION_ENCRYPTION,
    SIS_NTRU_COMMITMENTS,
    assign_research_sections,
)
from lattice_digest.models import make_paper_record


def _record(title: str, abstract: str, *, score: int = 86, label: str = "A"):
    return make_paper_record(
        title=title,
        abstract=abstract,
        source="golden",
        source_url="https://example.org/research-taxonomy",
        relevance_label=label,
        relevance_score=score,
        keywords_matched=[],
        taxonomy_tags=[],
    )


def test_lattice_privacy_fl_requires_lattice_or_pqc_anchor() -> None:
    positive = _record(
        "Differentially private federated fine-tuning with RLWE secure aggregation",
        "We combine DP-SGD, LLM fine-tuning, federated learning, and RLWE-based secure aggregation.",
    )
    generic = _record(
        "DP-SGD for LLM fine-tuning",
        "Differential privacy for federated fine-tuning of large language models using optimizer-level clipping and noise.",
        label="B",
        score=70,
    )

    assert LATTICE_PRIVACY_FL in assign_research_sections(positive)
    assert LATTICE_PRIVACY_FL not in assign_research_sections(generic)


def test_lattice_isomorphism_suppresses_graph_isomorphism_false_positive() -> None:
    positive = _record(
        "The Lattice Isomorphism Problem for Post-Quantum Cryptography",
        "We study structured lattice isomorphism, LIP and lattice automorphism as advanced lattice assumptions.",
    )
    graph = _record("Graph isomorphism for neural networks", "A graph isomorphism model for GNN architectures.", label="B", score=70)

    assert LATTICE_ISOMORPHISM in assign_research_sections(positive)
    assert LATTICE_ISOMORPHISM not in assign_research_sections(graph)


def test_registration_based_encryption_requires_crypto_context() -> None:
    positive = _record(
        "LWE-based registration-based encryption",
        "A public-key encryption with registration construction based on LWE.",
    )
    generic = _record(
        "User registration system for web accounts",
        "This paper studies account registration workflows and login UX.",
        label="B",
        score=70,
    )

    assert REGISTRATION_ENCRYPTION in assign_research_sections(positive)
    assert LWE_FAMILY in assign_research_sections(positive)
    assert REGISTRATION_ENCRYPTION not in assign_research_sections(generic)


def test_lattice_advanced_primitives_require_lattice_or_pqc_evidence() -> None:
    positive = _record(
        "Lattice-based anonymous credentials from Module-SIS commitments",
        "The primitive combines lattice-based zero-knowledge proof, anonymous credential, and Module-SIS commitment.",
    )
    generic_zk = _record(
        "Generic zero-knowledge proofs for anonymous credentials",
        "A generic zero-knowledge proof system for anonymous credentials using standard discrete-log style examples.",
        label="B",
        score=70,
    )

    positive_sections = assign_research_sections(positive)
    assert LATTICE_ADVANCED_PRIMITIVES in positive_sections
    assert SIS_NTRU_COMMITMENTS in positive_sections
    assert LATTICE_ADVANCED_PRIMITIVES not in assign_research_sections(generic_zk)
    assert GENERAL_CRYPTO_PRIVACY in assign_research_sections(generic_zk)


def test_lattice_secure_aggregation_for_fl_routes_to_privacy_section() -> None:
    record = _record(
        "Lattice-based secure aggregation for federated learning",
        "The protocol uses lattice-based homomorphic encryption for ML and secure aggregation in federated learning.",
    )

    sections = assign_research_sections(record)

    assert LATTICE_PRIVACY_FL in sections
    assert GENERAL_CRYPTO_PRIVACY in sections
