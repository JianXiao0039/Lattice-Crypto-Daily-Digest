from __future__ import annotations

from lattice_digest.pqc_radar import (
    SOURCE_AWARE_QUERY_ARCHITECTURE,
    generate_source_aware_dry_run_plan,
    lattice_centric_inclusion,
    query_families,
)


def test_dry_run_plans_never_enable_production_retrieval() -> None:
    plans = generate_source_aware_dry_run_plan()

    assert plans
    assert all(plan["production_retrieval_enabled"] is False for plan in plans)
    assert all(plan["architecture"] == SOURCE_AWARE_QUERY_ARCHITECTURE for plan in plans)
    assert all("no_global_broad_enablement" in plan["guardrails"] for plan in plans)

    families = query_families()
    assert all(family.production_retrieval_enabled is False for family in families.values())


def test_lattice_anchor_and_material_impact_guardrails_are_explicit() -> None:
    direct = lattice_centric_inclusion(
        "ML-KEM migration guidance",
        "The document discusses FIPS 203 and lattice-based KEM deployment.",
    )
    material = lattice_centric_inclusion(
        "PQC backup diversity update",
        "A non-lattice candidate changes the backup diversity position for standardized lattice schemes.",
    )
    irrelevant = lattice_centric_inclusion(
        "Generic quantum-safe marketing",
        "A vendor announces broad quantum-safe messaging without algorithm or lattice migration evidence.",
    )

    assert direct.accepted is True
    assert material.accepted is True
    assert material.todo_verify is True
    assert irrelevant.accepted is False


def test_status_security_and_deployment_guards_are_attached_to_plans() -> None:
    plans = generate_source_aware_dry_run_plan(["scheme_standardization"], ["arxiv", "openalex"])

    for plan in plans:
        assert "standardization_status_requires_S0" in plan["guardrails"]
        assert "technical_security_claim_requires_S1" in plan["guardrails"]
        assert "vendor_deployment_claim_requires_S2_or_official_release" in plan["guardrails"]
        assert "source_starved_state_must_be_explicit" in plan["guardrails"]
        assert "source_health_failure_must_remain_visible" in plan["guardrails"]
        assert "TODO_VERIFY" in plan["todo_verify_guard"]


def test_disabled_adapters_are_metadata_only() -> None:
    plans = generate_source_aware_dry_run_plan(
        ["scheme_standardization"],
        ["openalex", "crossref", "semantic_scholar", "official_status_sources", "vendor_library_sources"],
    )

    assert plans
    for plan in plans:
        assert plan["query_groups"] == []
        assert plan["queries"] == []
        assert plan["post_filter_terms"] == []
        assert plan["disabled_reason"]
        assert plan["production_retrieval_enabled"] is False
