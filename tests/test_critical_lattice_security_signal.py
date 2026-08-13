from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from lattice_digest.candidate_ledger import build_candidate_ledger, write_candidate_ledger
from lattice_digest.config import load_config_bundle
from lattice_digest.critical_security import analyze_critical_security_signal
from lattice_digest.critical_translation import (
    FORBIDDEN_ESCALATIONS,
    TODO_VERIFY_TRANSLATION,
    build_critical_claim_translation,
    validate_critical_translation,
)
from lattice_digest.digest import generate_markdown
from lattice_digest.models import make_paper_record, record_to_dict
from lattice_digest.radar_freshness import enrich_record_for_daily_radar
from lattice_digest.ranker import rank_records
from lattice_digest.run import _enabled_source_configs
from lattice_digest.source_queries import critical_query_requests, render_structured_query


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "critical_lattice_security_canaries.json"


def _fixtures() -> dict[str, dict]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload["canaries"]}


def _record(item: dict, **overrides):
    values = {
        "paper_id": item["id"],
        "title": item["title"],
        "authors": item.get("authors", ["Fixture Author"]),
        "abstract": item.get("abstract", ""),
        "conclusion": item.get("conclusion", ""),
        "source": "offline_canary",
        "source_url": f"offline://{item['id']}",
        "publication_date": item.get("publication_date", "2026-08-11"),
        "venue": item.get("venue", "Preprint"),
        "source_health": "yellow",
    }
    values.update(overrides)
    return make_paper_record(**values)


def _rank_and_enrich(item: dict, **overrides):
    cfg = load_config_bundle()
    ranked = rank_records([_record(item, **overrides)], cfg["taxonomy"], cfg["keywords"], cfg["negative"])[0]
    return ranked, enrich_record_for_daily_radar(ranked, date(2026, 8, 12))


def test_permanent_canary_corpus_has_required_shape() -> None:
    fixtures = _fixtures()
    assert len(fixtures) == 6
    assert "SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED" in fixtures
    assert sum(bool(item["expected_critical"]) for item in fixtures.values()) == 3


def test_simon_title_only_remains_weak() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    ranked, enriched = _rank_and_enrich(item, abstract="", conclusion="")
    assert (ranked.relevance_label, ranked.relevance_score) == ("D", 0)
    assert ranked.security_impact_severity == "UNKNOWN"
    assert enriched.suggested_action != "READ_AND_VERIFY_IMMEDIATELY"


def test_simon_complete_fixture_is_critical_but_unverified() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    ranked, enriched = _rank_and_enrich(item)
    assert (ranked.relevance_label, ranked.relevance_score) == ("A", 100)
    assert enriched.security_impact_severity == "CRITICAL"
    assert enriched.research_value_score == 100
    assert (enriched.evidence_confidence, enriched.recommendation_level) == ("TODO_VERIFY", "TODO_VERIFY")
    assert enriched.document_maturity == "preliminary_draft"
    assert enriched.suggested_action == "READ_AND_VERIFY_IMMEDIATELY"


def test_reduction_relations_are_directional_and_explainable() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    analysis = analyze_critical_security_signal(_record(item))
    relations = {entry["relation"] for entry in analysis.relations}
    assert {"SOLVES", "REDUCES_TO", "CLAIMED_CONSEQUENCE", "ALGORITHM_COMPLEXITY", "ALGORITHM_MODEL"} <= relations
    assert analysis.targets and "LWE" in analysis.targets
    reverse = _record(item, abstract="A polynomial-time quantum algorithm solves DCP. DCP reduces to LWE.", conclusion="")
    assert analyze_critical_security_signal(reverse).severity == "UNKNOWN"


def test_source_evidence_is_not_polluted_by_taxonomy_aliases() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    ranked, enriched = _rank_and_enrich(item)
    assert "lwe_sis_ntru_foundations" in ranked.inferred_topic_tags
    assert "lwe_sis_ntru_foundations" not in ranked.source_evidence_terms
    assert not any(term.lower() in {"sis", "module-sis", "msis"} for term in ranked.source_evidence_terms)
    assert "SIS/Module-SIS" not in enriched.user_relevance_tags


def test_positive_and_negative_canary_precision() -> None:
    fixtures = _fixtures()
    results = {key: _rank_and_enrich(item)[1] for key, item in fixtures.items()}
    assert results["DIRECT_TITLE_LWE_QUANTUM_CRYPTANALYSIS"].security_impact_severity == "CRITICAL"
    assert results["WEAK_TITLE_EDCP_REDUCTION_CONSEQUENCE"].security_impact_severity == "CRITICAL"
    assert results["GENERIC_QUANTUM_NEGATIVE"].security_impact_severity != "CRITICAL"
    assert results["GENERIC_FHE_NONCRITICAL"].security_impact_severity != "CRITICAL"
    assert results["GENERIC_CYBERSECURITY_NEGATIVE"].relevance_label == "D"


def test_strong_venue_cannot_manufacture_criticality() -> None:
    item = _fixtures()["GENERIC_CYBERSECURITY_NEGATIVE"]
    ranked, _ = _rank_and_enrich(item, source="iacr_eprint", venue="CRYPTO")
    assert ranked.security_impact_severity == "UNKNOWN"
    assert ranked.relevance_label != "A"


def test_critical_query_catalog_is_bounded_and_structured() -> None:
    config = load_config_bundle()["sources"]
    sources = {item["name"]: item for item in _enabled_source_configs(config)}
    requests = critical_query_requests(sources["arxiv"], syntax="arxiv")
    assert len(requests) == 7
    assert any('all:"dihedral coset problem"' in item.query_text for item in requests)
    assert all(item.query_text not in {"DCP", "quantum algorithm", "quantum computing"} for item in requests)
    assert 'all:"quantum algorithm"' in render_structured_query(config["critical_query_groups"][1], syntax="arxiv")


def test_source_specific_query_registration() -> None:
    sources = {item["name"]: item for item in _enabled_source_configs(load_config_bundle()["sources"])}
    assert len(critical_query_requests(sources["dblp"], syntax="free_text")) == 5
    assert len(critical_query_requests(sources["openalex"], syntax="plain")) == 7
    assert len(critical_query_requests(sources["crossref"], syntax="plain")) == 7
    assert len(critical_query_requests(sources["semantic_scholar"], syntax="plain")) == 7


def test_candidate_ledger_records_drop_stage_and_route(tmp_path: Path) -> None:
    fixtures = _fixtures()
    positive = _rank_and_enrich(fixtures["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"])[0]
    negative = _rank_and_enrich(fixtures["GENERIC_QUANTUM_NEGATIVE"])[0]
    payload = build_candidate_ledger(
        [positive, negative], [positive, negative], [positive, negative], [positive], [positive], [positive],
        [{"source": "offline_canary", "health_status": "yellow"}], date(2026, 8, 11),
    )
    rows = {row["identifier"]: row for row in payload["candidates"]}
    assert rows[positive.paper_id]["final_route"] == "included"
    assert rows[negative.paper_id]["drop_stage"] == "RELEVANCE"
    path = write_candidate_ledger(payload, tmp_path, date(2026, 8, 11))
    assert path == tmp_path / "audits" / "worktree" / "candidate-retrieval-ledger-2026-08-11.json"
    assert json.loads(path.read_text(encoding="utf-8"))["artifact_role"] == "scratch_diagnostic_non_authoritative"


def test_translation_preserves_terms_formula_numbers_and_qualifiers() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    record = _record(item)
    translated = build_critical_claim_translation(record)
    check = validate_critical_translation(" ".join([record.title, record.abstract, record.conclusion, record.venue or ""]), translated)
    assert check.status == "VERIFIED_TERM_LOCKS"
    assert all(token in translated for token in ("二面体陪集问题", "多项式时间量子算法", "初步草稿", "LWE", "SVP"))
    assert "1/O(log n)" in translated
    assert "TODO_VERIFY" in translated and "不能据此断言" in translated


def test_translation_failure_is_visible_and_english_remains_available() -> None:
    source = "A Preliminary Draft claims a polynomial-time quantum algorithm for LWE with faulty sample rate 1/O(log n)."
    check = validate_critical_translation(source, "该论文证明了一个算法。")
    assert check.status == TODO_VERIFY_TRANSLATION
    assert any(item.startswith("term:") or item.startswith("token:") for item in check.missing)
    assert source.startswith("A Preliminary Draft")


def test_forbidden_security_claim_escalation_is_detected_and_not_generated() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    translated = build_critical_claim_translation(_record(item))
    assert not any(phrase in translated for phrase in FORBIDDEN_ESCALATIONS)
    check = validate_critical_translation(item["abstract"], "ML-KEM 已被攻破")
    assert "ML-KEM 已被攻破" in check.forbidden


def test_critical_markdown_alert_is_early_and_complete() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    ranked, _ = _rank_and_enrich(item)
    markdown = generate_markdown([ranked], date(2026, 8, 12))
    alert = markdown.index("🚨 潜在关键格密码安全信号 · TODO_VERIFY")
    audit = markdown.index("#### Audit Details")
    assert alert < audit
    assert "READ_AND_VERIFY_IMMEDIATELY" in markdown
    assert "What it does NOT establish" in markdown
    assert "English source text / evidence" in markdown
    assert "ML-KEM、ML-DSA、标准化 Module-LWE" in markdown


def test_ordinary_markdown_readability_is_unchanged() -> None:
    item = _fixtures()["GENERIC_FHE_NONCRITICAL"]
    ranked, _ = _rank_and_enrich(item)
    markdown = generate_markdown([ranked], date(2026, 8, 12))
    assert "🚨 潜在关键格密码安全信号" not in markdown
    assert "#### Recommendation" in markdown


def test_additive_schema_serializes_with_backward_compatible_defaults() -> None:
    item = _fixtures()["GENERIC_FHE_NONCRITICAL"]
    payload = record_to_dict(_record(item))
    assert payload["security_impact_severity"] == "UNKNOWN"
    assert payload["source_evidence_terms"] == []
    assert payload["translation_fidelity_status"] == "not_applicable"


def test_freshness_policy_remains_unchanged_for_incident_date() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    _, enriched = _rank_and_enrich(item)
    assert enriched.freshness_bucket == "primary_today_new"
    assert enriched.selected_date_basis == "publication_date"


def test_simon_abstract_without_reduction_does_not_invent_direction() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    abstract = "This preliminary draft claims a polynomial-time quantum algorithm for DCP and separately discusses LWE."
    ranked, _ = _rank_and_enrich(item, abstract=abstract, conclusion="")
    assert ranked.security_impact_severity == "UNKNOWN"


def test_isolated_consequence_word_is_not_enough() -> None:
    item = _fixtures()["GENERIC_QUANTUM_NEGATIVE"]
    analysis = analyze_critical_security_signal(_record(item, abstract="A quantum algorithm may threaten runtime assumptions."))
    assert analysis.severity == "UNKNOWN"


def test_generic_fhe_can_be_relevant_without_critical_cryptanalysis() -> None:
    item = _fixtures()["GENERIC_FHE_NONCRITICAL"]
    ranked, enriched = _rank_and_enrich(item)
    assert ranked.relevance_label in {"A", "B", "C"}
    assert enriched.security_impact_severity == "UNKNOWN"
    assert enriched.suggested_action != "READ_AND_VERIFY_IMMEDIATELY"


def test_critical_risk_flags_keep_preliminary_and_no_standard_break() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    _, enriched = _rank_and_enrich(item)
    assert "preliminary_draft" in enriched.TODO_VERIFY_flags
    assert "no_parameter_specific_standard_break_established" in enriched.TODO_VERIFY_flags
    assert "critical_security_claim_todo_verify" in enriched.recommendation_risk_flags


def test_critical_evidence_basis_separates_inference() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    _, enriched = _rank_and_enrich(item)
    assert "source_evidence_terms" in enriched.recommendation_evidence_basis
    assert "inferred_topic_tags" in enriched.recommendation_evidence_basis
    assert "source_grounded_reduction_relations" in enriched.recommendation_evidence_basis


def test_query_exact_problem_family_is_not_bare_acronym() -> None:
    config = load_config_bundle()["sources"]
    source = {item["name"]: item for item in _enabled_source_configs(config)}["arxiv"]
    request = next(item for item in critical_query_requests(source, syntax="arxiv") if item.family_id == "exact_dihedral_problem_family")
    assert request.query_text.startswith("(")
    assert 'all:"dihedral coset problem"' in request.query_text
    assert request.query_text != "all:DCP"


def test_query_consequence_family_requires_both_groups() -> None:
    spec = {"id": "bounded", "all_of_groups": [["quantum algorithm"], ["LWE"]]}
    assert render_structured_query(spec, syntax="arxiv") == 'all:"quantum algorithm" AND all:LWE'
    assert render_structured_query(spec, syntax="plain") == '"quantum algorithm" AND LWE'
    free_text = critical_query_requests({"critical_query_groups": [spec]}, syntax="free_text")
    assert [item.query_text for item in free_text] == ['"quantum algorithm" LWE']


def test_critical_queries_precede_legacy_queries_in_arxiv_adapter_config() -> None:
    config = load_config_bundle()["sources"]
    source = {item["name"]: item for item in _enabled_source_configs(config)}["arxiv"]
    requests = critical_query_requests(source, syntax="arxiv")
    assert requests[0].family_id == "exact_dihedral_problem_family"


def test_candidate_ledger_does_not_expose_api_keys(tmp_path: Path) -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    ranked, _ = _rank_and_enrich(item, source_query_text='"quantum algorithm" AND LWE')
    payload = build_candidate_ledger([ranked], [ranked], [ranked], [ranked], [ranked], [ranked], [], date(2026, 8, 11))
    path = write_candidate_ledger(payload, tmp_path, date(2026, 8, 11))
    text = path.read_text(encoding="utf-8")
    assert "API_KEY" not in text and "SEMANTIC_SCHOLAR_API_KEY" not in text


def test_candidate_ledger_freshness_drop_is_diagnosable() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    ranked, _ = _rank_and_enrich(item)
    payload = build_candidate_ledger([ranked], [ranked], [], [], [], [], [], date(2026, 8, 11))
    row = payload["candidates"][0]
    assert (row["drop_stage"], row["final_route"]) == ("FRESHNESS", "dropped")


def test_critical_translation_exposes_status_and_source_text_in_markdown() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    ranked, _ = _rank_and_enrich(item)
    markdown = generate_markdown([ranked], date(2026, 8, 12))
    assert "Translation fidelity：VERIFIED_TERM_LOCKS" in markdown
    assert "polynomial-time quantum algorithm" in markdown
    assert "1/O(log n)" in markdown


def test_noncritical_translation_guard_is_not_applied() -> None:
    item = _fixtures()["GENERIC_FHE_NONCRITICAL"]
    _, enriched = _rank_and_enrich(item)
    assert enriched.translation_fidelity_status == "not_applicable"
    assert enriched.critical_claim_zh == ""


def test_serialized_critical_relations_retain_evidence_field() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    ranked, _ = _rank_and_enrich(item)
    payload = record_to_dict(ranked)
    assert payload["critical_signal_relations"]
    assert {row["evidence_field"] for row in payload["critical_signal_relations"]} == {"source_content"}


def test_faulty_sample_rate_is_detail_not_standalone_critical_signal() -> None:
    item = _fixtures()["GENERIC_QUANTUM_NEGATIVE"]
    analysis = analyze_critical_security_signal(_record(item, abstract="A faulty sample rate 1/O(log n) is evaluated."))
    assert analysis.severity == "UNKNOWN"
    assert "faulty sample rate" in analysis.source_evidence_terms


def test_model_security_impact_allowed_values_for_pipeline_outputs() -> None:
    fixtures = _fixtures()
    observed = {_rank_and_enrich(item)[1].security_impact_severity for item in fixtures.values()}
    assert observed <= {"CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"}


def test_no_unsupported_standard_break_text_in_critical_explanation() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    _, enriched = _rank_and_enrich(item)
    text = " ".join([enriched.critical_signal_explanation, enriched.critical_claim_zh])
    assert "已被攻破" not in text
    assert "不能据此断言" in text


def test_simon_author_date_and_maturity_survive_fixture_pipeline() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    _, enriched = _rank_and_enrich(item)
    assert enriched.authors == ["Daniel R. Simon"]
    assert enriched.publication_date == "2026-08-11"
    assert enriched.document_maturity == "preliminary_draft"


def test_direct_title_lwe_positive_keeps_claim_qualifier() -> None:
    item = _fixtures()["DIRECT_TITLE_LWE_QUANTUM_CRYPTANALYSIS"]
    _, enriched = _rank_and_enrich(item)
    assert enriched.security_impact_severity == "CRITICAL"
    assert enriched.evidence_confidence == "TODO_VERIFY"
    assert "claimed" in analyze_critical_security_signal(_record(item)).qualifiers


def test_edcp_positive_requires_explicit_lwe_consequence() -> None:
    item = _fixtures()["WEAK_TITLE_EDCP_REDUCTION_CONSEQUENCE"]
    ranked, enriched = _rank_and_enrich(item)
    assert ranked.relevance_score == 100
    assert enriched.suggested_action == "READ_AND_VERIFY_IMMEDIATELY"


def test_candidate_ledger_schema_has_complete_diagnostic_chain() -> None:
    payload = build_candidate_ledger([], [], [], [], [], [], [], date(2026, 8, 11))
    assert payload["diagnostic_chain"] == ["SOURCE", "QUERY", "NORMALIZATION", "RELEVANCE", "FRESHNESS", "ROUTE"]


def test_candidate_ledger_records_zero_result_query_attempts() -> None:
    attempts = [{"source_family": "arxiv", "query_family": "dcp_lattice", "query_text": "all:DCP AND all:lattice", "status": "success", "raw_candidates": 0}]
    payload = build_candidate_ledger([], [], [], [], [], [], [], date(2026, 8, 11), attempts)
    assert payload["query_attempts"] == attempts


def test_candidate_ledger_requires_external_output_root() -> None:
    import lattice_digest.run as run_module

    try:
        run_module.main(["--candidate-ledger", "--dry-run"])
    except SystemExit as exc:
        assert "explicit external --output-root" in str(exc)
    else:
        raise AssertionError("candidate ledger must not default to the authoritative project root")


def test_critical_markdown_first_screen_order() -> None:
    item = _fixtures()["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    ranked, _ = _rank_and_enrich(item)
    markdown = generate_markdown([ranked], date(2026, 8, 12))
    labels = [
        "🚨 潜在关键格密码安全信号",
        "What it claims",
        "Why it matters",
        "What remains unverified",
        "What it does NOT establish",
        "Recommended action",
        "Chinese faithful translation",
        "English source text / evidence",
        "#### Audit Details",
    ]
    positions = [markdown.index(label) for label in labels]
    assert positions == sorted(positions)
