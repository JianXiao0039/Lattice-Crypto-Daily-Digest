from __future__ import annotations

from lattice_digest.pqc_radar import (
    EvidenceTier,
    evidence_tier_can_finalize_security_claim,
    evidence_tier_can_verify_status,
    evidence_tier_requires_todo_verify,
    hawk_dynamic_status,
)


def test_hawk_dynamic_status_is_source_backed_and_replaceable() -> None:
    status = hawk_dynamic_status()

    assert status.scheme == "HAWK"
    assert status.process_name == "NIST Additional Digital Signature Schemes"
    assert status.round_or_stage == "Round 3 candidate"
    assert status.current_status == "active Round 3 candidate"
    assert status.evidence_tier == EvidenceTier.S0
    assert "NIST" in status.primary_source
    assert status.todo_verify is False


def test_only_s0_can_verify_standardization_status() -> None:
    assert evidence_tier_can_verify_status(EvidenceTier.S0)
    for tier in (EvidenceTier.S1, EvidenceTier.S2, EvidenceTier.S3, EvidenceTier.S4):
        assert not evidence_tier_can_verify_status(tier)


def test_s1_is_required_for_technical_security_claims() -> None:
    assert evidence_tier_can_finalize_security_claim(EvidenceTier.S1)
    assert not evidence_tier_can_finalize_security_claim(EvidenceTier.S4)


def test_discovery_only_evidence_keeps_todo_verify() -> None:
    assert evidence_tier_requires_todo_verify(EvidenceTier.S4)
    assert evidence_tier_requires_todo_verify(EvidenceTier.S3)
    assert not evidence_tier_requires_todo_verify(EvidenceTier.S0)
