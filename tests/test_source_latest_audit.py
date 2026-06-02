from __future__ import annotations

from lattice_digest.config import load_config_bundle
from lattice_digest.source_latest_audit import audit_latest_capabilities, render_latest_capability_table


def test_source_latest_audit_classifies_configured_sources() -> None:
    configs = load_config_bundle(None)
    capabilities = audit_latest_capabilities(configs["sources"])
    by_source = {capability.source: capability for capability in capabilities}

    assert by_source["iacr_eprint"].status == "supports latest enumeration"
    assert "RSS" in by_source["iacr_eprint"].mechanism
    assert by_source["iacr_eprint"].manual_flag == "--include-latest-sources"
    assert by_source["arxiv"].status == "query search only"
    assert by_source["openalex"].status == "query search only"
    assert by_source["crossref"].status == "query search only"
    assert by_source["dblp"].status == "query search only"
    assert by_source["semantic_scholar"].status == "query search only"
    assert "SEMANTIC_SCHOLAR_API_KEY" in by_source["semantic_scholar"].notes


def test_source_latest_audit_report_table_is_deterministic() -> None:
    configs = load_config_bundle(None)
    table = render_latest_capability_table(audit_latest_capabilities(configs["sources"]))

    assert "| Source | Capability | Mechanism | Manual flag | Notes |" in table
    assert "iacr_eprint" in table
    assert "supports latest enumeration" in table
    assert "query search only" in table
    assert "metadata enrichment only" not in table
    assert "ghp_" not in table
    assert "github_pat_" not in table
    assert "sk-" not in table
