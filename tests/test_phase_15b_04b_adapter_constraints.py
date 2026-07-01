from __future__ import annotations

from lattice_digest.pqc_radar import generate_source_aware_dry_run_plan, source_aware_adapter_constraints


def _single(adapter_id: str) -> dict[str, object]:
    return generate_source_aware_dry_run_plan(["scheme_standardization"], [adapter_id])[0]


def test_adapter_constraint_registry_covers_design_review_surface() -> None:
    constraints = source_aware_adapter_constraints()

    assert set(constraints) == {
        "arxiv",
        "dblp",
        "iacr_eprint",
        "openalex",
        "crossref",
        "semantic_scholar",
        "official_status_sources",
        "vendor_library_sources",
    }
    assert constraints["arxiv"].status == "guarded_dry_run_mapping"
    assert constraints["dblp"].status == "guarded_dry_run_mapping"
    assert constraints["iacr_eprint"].status == "guarded_post_filter_planning"
    assert constraints["openalex"].status == "disabled_live_behavior"
    assert constraints["official_status_sources"].status == "out_of_scope"


def test_arxiv_plan_uses_bounded_query_groups_without_network_fields() -> None:
    plan = _single("arxiv")

    assert plan["status"] == "guarded_dry_run_mapping"
    assert plan["output_schema"] == "query_groups"
    assert plan["query_groups"]
    assert plan["max_query_count"] == len(plan["query_groups"])
    assert plan["max_query_count"] <= 4
    assert plan["queries"] == []
    assert plan["production_retrieval_enabled"] is False


def test_dblp_plan_uses_bounded_query_list() -> None:
    plan = _single("dblp")

    assert plan["status"] == "guarded_dry_run_mapping"
    assert plan["output_schema"] == "queries"
    assert len(plan["queries"]) == 1
    assert "standardization" in plan["queries"][0]
    assert any(anchor in plan["queries"][0] for anchor in ("FN-DSA", "HAWK", "ML-KEM", "ML-DSA"))
    assert plan["query_groups"] == []
    assert plan["production_retrieval_enabled"] is False


def test_iacr_plan_is_post_filter_only() -> None:
    plan = _single("iacr_eprint")

    assert plan["status"] == "guarded_post_filter_planning"
    assert plan["output_schema"] == "post_filter_terms"
    assert plan["post_filter_terms"]
    assert plan["query_groups"] == []
    assert plan["queries"] == []
    assert plan["max_query_count"] == 0
    assert plan["production_retrieval_enabled"] is False


def test_disabled_and_out_of_scope_adapters_do_not_emit_live_queries() -> None:
    for adapter_id in ("openalex", "crossref", "semantic_scholar", "official_status_sources", "vendor_library_sources"):
        plan = _single(adapter_id)

        assert plan["status"] in {"disabled_live_behavior", "out_of_scope"}
        assert plan["disabled_reason"]
        assert plan["query_groups"] == []
        assert plan["queries"] == []
        assert plan["post_filter_terms"] == []
        assert plan["production_retrieval_enabled"] is False
