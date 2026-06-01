from __future__ import annotations

from lattice_digest.digest_sections import (
    GENERAL_CRYPTO_PRIVACY,
    LATTICE_ADVANCED_PRIMITIVES,
    LATTICE_ISOMORPHISM,
    LATTICE_PRIVACY_FL,
    REGISTRATION_ENCRYPTION,
    assign_research_sections,
)
from lattice_digest.models import make_paper_record


def _record(title: str, abstract: str, *, label: str = "A", score: int = 86):
    return make_paper_record(
        title=title,
        abstract=abstract,
        source="manual_run_fixture",
        source_url="https://example.org/manual-run-calibration",
        relevance_label=label,
        relevance_score=score,
        keywords_matched=[],
        taxonomy_tags=[],
    )


def test_lattice_pqc_registration_based_encryption_true_positives() -> None:
    cases = [
        ("LWE-based registration-based encryption", "A registration-based encryption construction from LWE."),
        (
            "Post-quantum registration-based encryption from lattices",
            "A PQC registration-based encryption primitive from lattices.",
        ),
    ]
    for title, abstract in cases:
        assert REGISTRATION_ENCRYPTION in assign_research_sections(_record(title, abstract))


def test_generic_registration_false_positives_do_not_enter_rbe() -> None:
    cases = [
        ("Registration-based access control system", "A generic access-control workflow for enterprise user registration."),
        ("User account registration with encryption", "A web account registration system that encrypts stored profiles."),
        ("Medical image registration with encrypted storage", "A medical image registration pipeline stores images encrypted at rest."),
        ("Registration-based encryption for databases", "A generic registration-based encryption interface for database middleware."),
        ("Certificate registration with encrypted audit logs", "A certificate registration system with encrypted audit logs."),
    ]
    for title, abstract in cases:
        assert REGISTRATION_ENCRYPTION not in assign_research_sections(_record(title, abstract, label="B", score=70))


def test_lattice_privacy_fl_true_positives() -> None:
    cases = [
        ("RLWE-based secure aggregation for federated learning", "RLWE-based secure aggregation for federated learning."),
        (
            "Fully homomorphic encryption for private LLM fine-tuning",
            "A private LLM fine-tuning protocol based on RLWE fully homomorphic encryption.",
        ),
        (
            "Lattice-based secure aggregation for federated learning",
            "A lattice-based secure aggregation protocol for federated learning.",
        ),
    ]
    for title, abstract in cases:
        assert LATTICE_PRIVACY_FL in assign_research_sections(_record(title, abstract))


def test_generic_privacy_fl_false_positives_do_not_enter_lattice_privacy() -> None:
    cases = [
        ("DP-SGD for LLM fine-tuning", "Generic DP-SGD for fine-tuning large language models."),
        ("Federated learning for LLMs", "A generic federated learning optimizer for LLMs."),
        ("Generic secure aggregation", "A generic secure aggregation protocol for distributed statistics."),
    ]
    for title, abstract in cases:
        assert LATTICE_PRIVACY_FL not in assign_research_sections(_record(title, abstract, label="B", score=70))


def test_lattice_isomorphism_true_positives() -> None:
    cases = [
        ("Lattice isomorphism problem for post-quantum cryptography", "The LIP appears in a lattice/PQC context."),
        ("Structured lattice isomorphism", "We study lattice automorphism and isomorphism of lattices."),
    ]
    for title, abstract in cases:
        assert LATTICE_ISOMORPHISM in assign_research_sections(_record(title, abstract))


def test_isomorphism_and_registration_false_positives_do_not_enter_lattice_isomorphism() -> None:
    cases = [
        ("Graph isomorphism algorithm", "A graph isomorphism algorithm for sparse graphs."),
        ("Code isomorphism problem", "The code isomorphism problem for linear codes."),
        ("Point cloud registration", "A point cloud registration method using neural isomorphism features."),
    ]
    for title, abstract in cases:
        assert LATTICE_ISOMORPHISM not in assign_research_sections(_record(title, abstract, label="B", score=70))


def test_lattice_advanced_primitive_true_positives() -> None:
    cases = [
        ("Module-SIS chameleon hash", "A Module-SIS chameleon hash and commitment primitive."),
        ("SIS-based commitment", "A SIS-based commitment scheme with parameter analysis."),
        ("Lattice-based anonymous credential", "A lattice-based anonymous credential with zero-knowledge proof."),
        ("Lattice-based ring signature", "A lattice-based ring signature from module lattices."),
        ("LWE-based functional encryption", "A functional encryption primitive based on LWE."),
        ("Lattice-based zero-knowledge proof", "A lattice-based zero-knowledge proof for Module-SIS relations."),
    ]
    for title, abstract in cases:
        assert LATTICE_ADVANCED_PRIMITIVES in assign_research_sections(_record(title, abstract))


def test_generic_advanced_primitive_false_positives_stay_general() -> None:
    cases = [
        ("Generic zero-knowledge proof", "A generic zero-knowledge proof for discrete-log relations."),
        ("Generic anonymous credential", "An anonymous credential system with standard assumptions."),
        ("Generic commitment scheme", "A commitment scheme for application protocols."),
        ("Generic functional encryption", "A functional encryption survey with standard assumptions."),
    ]
    for title, abstract in cases:
        sections = assign_research_sections(_record(title, abstract, label="B", score=70))

        assert LATTICE_ADVANCED_PRIMITIVES not in sections
        assert GENERAL_CRYPTO_PRIVACY in sections or REGISTRATION_ENCRYPTION not in sections
