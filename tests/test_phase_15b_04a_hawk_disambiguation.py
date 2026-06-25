from __future__ import annotations

from lattice_digest.pqc_radar import classify_hawk_context, lattice_centric_inclusion


def test_hawk_positive_fixtures_are_accepted() -> None:
    fixtures = [
        (
            "NIST advances HAWK to Round 3",
            "The HAWK post-quantum digital signature candidate remains in the NIST additional signatures process.",
        ),
        (
            "HAWK implementation benchmark on Cortex-M",
            "Constant-time signing and verification for the lattice signature are measured.",
        ),
        (
            "Cryptanalysis of HAWK parameters",
            "A lattice reduction analysis studies NTRU and MLIP assumptions.",
        ),
        (
            "Side-channel evaluation of Hawk key generation",
            "The signature implementation is tested for power analysis leakage.",
        ),
    ]

    for title, body in fixtures:
        decision = classify_hawk_context(title, body)
        assert decision.accepted, (title, decision)
        assert decision.matched_crypto_contexts


def test_hawk_negative_fixtures_are_rejected() -> None:
    fixtures = [
        ("Hawk migration patterns in urban birds", "Wildlife observers track bird behavior."),
        ("Hawk sports team wins final", "A team report with no cryptography."),
        ("HAWK malware-detection model improves recall", "Graph neural network malware detection benchmark."),
        ("Hawk radar system upgrade announced", "Missile defense radar procurement."),
    ]

    for title, body in fixtures:
        decision = classify_hawk_context(title, body)
        assert not decision.accepted, (title, decision)
        assert decision.reason in {
            "hawk_negative_context",
            "hawk_conflicting_negative_context",
            "hawk_without_crypto_coanchor",
        }


def test_hawk_token_alone_is_rejected_across_case_and_punctuation() -> None:
    for title in ["HAWK", "hawk.", "A note on Hawk"]:
        decision = classify_hawk_context(title)
        assert not decision.accepted
        assert decision.reason == "hawk_without_crypto_coanchor"


def test_borderline_lattice_impact_fixtures_are_todo_verify_when_non_lattice() -> None:
    hqc = lattice_centric_inclusion(
        "HQC selection changes PQC diversity planning",
        "The guidance compares backup roles for ML-KEM migration.",
    )
    slh_dsa = lattice_centric_inclusion(
        "SLH-DSA guidance paired with ML-DSA migration",
        "The policy changes certificate planning for ML-DSA.",
    )
    hybrid = lattice_centric_inclusion(
        "Hybrid key exchange deployment",
        "The body names ML-KEM for a TLS migration.",
    )
    generic = lattice_centric_inclusion(
        "Quantum-safe product launch",
        "Marketing material does not name any algorithm or lattice assumption.",
    )

    assert hqc.accepted and "ml-kem" in {item.lower() for item in hqc.lattice_anchors}
    assert slh_dsa.accepted and "ml-dsa" in {item.lower() for item in slh_dsa.lattice_anchors}
    assert hybrid.accepted and "ml-kem" in {item.lower() for item in hybrid.lattice_anchors}
    assert not generic.accepted
