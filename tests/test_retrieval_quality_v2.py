from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from lattice_digest.candidate_ledger import build_candidate_ledger
from lattice_digest.config import load_config_bundle
from lattice_digest.dedup import deduplicate
from lattice_digest.models import make_paper_record
from lattice_digest.retrieval_benchmark import (
    REQUIRED_CATEGORIES,
    assert_hard_retrieval_gates,
    evaluate_retrieval_benchmark,
    load_retrieval_benchmark,
)
from lattice_digest.run import _enabled_source_configs, _filter_by_source_role
from lattice_digest.source_queries import (
    QueryRequest,
    critical_query_requests,
    query_portfolio_for_source,
    stable_query_id,
)
from lattice_digest.source_roles import SourceRole, serialized_source_roles
from lattice_digest.sources.base import FetchContext


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "tests" / "fixtures" / "retrieval_benchmark_v1.json"


def _sources() -> dict[str, dict]:
    return {item["name"]: item for item in _enabled_source_configs(load_config_bundle()["sources"])}


@pytest.mark.parametrize(
    ("source", "primary_role"),
    [
        ("iacr_eprint", SourceRole.DISCOVERY_PRIMARY.value),
        ("arxiv", SourceRole.DISCOVERY_PRIMARY.value),
        ("openalex", SourceRole.DISCOVERY_SECONDARY.value),
        ("semantic_scholar", SourceRole.DISCOVERY_SECONDARY.value),
        ("dblp", SourceRole.IDENTIFIER_RESOLUTION.value),
        ("crossref", SourceRole.METADATA_ENRICHMENT.value),
    ],
)
def test_source_roles_are_explicit_and_deterministic(source: str, primary_role: str) -> None:
    config = _sources()[source]
    first = serialized_source_roles(config)
    assert first == serialized_source_roles(config)
    assert first[0] == primary_role


def test_crossref_and_dblp_are_not_primary_discovery() -> None:
    sources = _sources()
    for source in ("crossref", "dblp"):
        roles = serialized_source_roles(sources[source])
        assert SourceRole.DISCOVERY_PRIMARY.value not in roles
    assert SourceRole.METADATA_ENRICHMENT.value in serialized_source_roles(sources["crossref"])
    assert SourceRole.VENUE_AUTHORITY.value in serialized_source_roles(sources["dblp"])


def test_query_ids_are_stable_and_source_specific() -> None:
    assert stable_query_id("arxiv", "dcp_lattice", version="v2a-1") == "Q-ARXIV-DCP-LATTICE-V2A-1"
    assert stable_query_id("crossref", "dcp_lattice", version="v2a-1") != stable_query_id(
        "arxiv", "dcp_lattice", version="v2a-1"
    )


@pytest.mark.parametrize("source", ["arxiv", "dblp", "openalex", "crossref", "semantic_scholar", "iacr_eprint"])
def test_query_portfolio_has_required_metadata(source: str) -> None:
    portfolio = query_portfolio_for_source(_sources()[source])
    assert portfolio
    assert len({item.query_id for item in portfolio}) == len(portfolio)
    for item in portfolio:
        diagnostic = item.to_diagnostic_dict()
        assert diagnostic["source_family"] == source
        assert diagnostic["query_expression_hash"]
        assert diagnostic["intent"]
        assert diagnostic["compatibility_version"] == "v2a-1"
        assert diagnostic["enabled"] is True


def test_narrow_p0_queries_remain_and_no_generic_quantum_flood() -> None:
    requests = critical_query_requests(_sources()["arxiv"], syntax="arxiv")
    families = {item.family_id for item in requests}
    assert {"exact_dihedral_problem_family", "quantum_lwe_consequence", "quantum_svp_consequence", "regev_reduction_lattice"} <= families
    texts = {item.query_text.strip().lower() for item in requests}
    assert "quantum algorithm" not in texts
    assert "quantum computing" not in texts
    assert "dcp" not in texts


def test_free_text_critical_queries_do_not_create_one_long_accidental_query() -> None:
    requests = critical_query_requests(_sources()["crossref"], syntax="free_text")
    assert len(requests) > 7
    assert all(item.query_text.count(" ") < 8 for item in requests)


def test_disabled_query_definition_is_not_returned() -> None:
    request = QueryRequest("disabled", "LWE", enabled=False, source_family="arxiv")
    assert request.enabled is False


def _context(tmp_path: Path) -> FetchContext:
    context = FetchContext(tmp_path, datetime(2026, 8, 11, tzinfo=timezone.utc), False)
    context.register_source(_sources()["arxiv"])
    return context


def test_query_attempt_zero_hit_and_source_roles_are_observable(tmp_path: Path) -> None:
    context = _context(tmp_path)
    request = query_portfolio_for_source(_sources()["arxiv"])[0]
    attempt_id = context.begin_query_attempt("arxiv", request)
    context.finish_query_attempt(attempt_id, status="success", raw_candidates=0)
    attempt = context.query_attempts[0]
    assert attempt["query_id"] == request.query_id
    assert attempt["source_role"] == SourceRole.DISCOVERY_PRIMARY.value
    assert attempt["coverage_semantics"] == "OBSERVED_RESULTS"
    assert any(event["decision"] == "QUERY_ZERO_HIT" for event in context.route_events)


def test_rate_limit_is_unknown_coverage_not_semantic_negative(tmp_path: Path) -> None:
    context = _context(tmp_path)
    request = query_portfolio_for_source(_sources()["arxiv"])[0]
    attempt_id = context.begin_query_attempt("arxiv", request)
    context.finish_query_attempt(attempt_id, status="rate_limited", raw_candidates=None, error_category="rate_limit")
    assert context.query_attempts[0]["coverage_semantics"] == "UNKNOWN_COVERAGE"
    assert context.route_events[0]["decision"] == "RATE_LIMITED"
    assert "PAPER_NOT_PRESENT" not in str(context.query_attempts + context.route_events)


def test_raw_parse_failure_has_terminal_trace(tmp_path: Path) -> None:
    context = _context(tmp_path)
    request = query_portfolio_for_source(_sources()["arxiv"])[0]
    attempt = context.begin_query_attempt("arxiv", request)
    occurrence = context.record_raw_occurrence(
        "arxiv", attempt, raw_title="", parser_result="RAW_PARSE_FAILED", parser_failure_reason="missing title", normalization_eligible=False
    )
    assert context.raw_occurrences[0]["raw_occurrence_id"] == occurrence
    assert context.route_events[0]["decision"] == "RAW_PARSE_FAILED"
    assert context.route_events[0]["terminal"] is True


def test_normalized_candidate_records_title_only_evidence(tmp_path: Path) -> None:
    context = _context(tmp_path)
    request = query_portfolio_for_source(_sources()["arxiv"])[0]
    attempt = context.begin_query_attempt("arxiv", request)
    occurrence = context.record_raw_occurrence("arxiv", attempt, raw_title="DBLP title", abstract_present=False)
    record = make_paper_record(title="DBLP title", source="dblp", source_url="https://dblp.org/x")
    context.record_normalized_candidate(occurrence, record)
    assert context.normalized_candidates[0]["evidence_availability"] == "TITLE_ONLY"
    assert any(event["decision"] == "NO_ABSTRACT" for event in context.route_events)


def test_multi_query_provenance_is_preserved_without_ranking_inflation(tmp_path: Path) -> None:
    context = _context(tmp_path)
    requests = query_portfolio_for_source(_sources()["arxiv"])[:2]
    record = make_paper_record(
        title="LWE Result", abstract="LWE cryptography", source="arxiv", source_url="https://arxiv.org/abs/2608.1", arxiv_id="2608.1"
    )
    for request in requests:
        attempt = context.begin_query_attempt("arxiv", request)
        occurrence = context.record_raw_occurrence("arxiv", attempt, raw_title=record.title, source_url=record.source_url, abstract_present=True)
        context.record_normalized_candidate(occurrence, record)
    canonical = deduplicate([record, record])
    payload = build_candidate_ledger(
        [record, record], [record, record], [record, record], [record, record], canonical, canonical,
        [{"source": "arxiv", "health_status": "green"}], date(2026, 8, 11), context.query_attempts,
        run_id=context.run_id, run_started_at=context.run_started_at, raw_occurrences=context.raw_occurrences,
        normalized_candidates=context.normalized_candidates, route_events=context.route_events,
    )
    assert len(canonical) == 1
    assert len(payload["canonical_candidates"]) == 1
    assert len(payload["canonical_candidates"][0]["query_attempt_ids"]) == 2
    assert payload["traceability"]["percentage"] == 100.0


def test_ledger_v2_is_scratch_only_and_no_secrets(tmp_path: Path) -> None:
    context = _context(tmp_path)
    payload = build_candidate_ledger([], [], [], [], [], [], [], date(2026, 8, 11), run_id=context.run_id)
    assert payload["artifact_role"] == "scratch_diagnostic_non_authoritative"
    assert payload["privacy_contract"] == "no_credentials_tokens_auth_headers_or_secrets"
    assert "data/" not in str(payload) and "digests/" not in str(payload)


def test_retrieval_benchmark_is_exactly_frozen_and_complete() -> None:
    payload = load_retrieval_benchmark(BENCHMARK)
    assert payload["frozen"] is True
    assert payload["record_count"] == 100
    assert set(payload["categories"]) == REQUIRED_CATEGORIES
    kinds = {item["record_kind"] for item in payload["records"]}
    assert kinds == {"incident_canary", "synthetic_control"}


def test_simon_canary_is_preserved_in_retrieval_benchmark() -> None:
    payload = load_retrieval_benchmark(BENCHMARK)
    simon = next(item for item in payload["records"] if item["fixture_id"] == "SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED")
    assert simon["expected"]["critical"] is True
    assert simon["expected"]["security_impact"] == "CRITICAL"
    assert simon["expected"]["action_class"] == "READ_AND_VERIFY_IMMEDIATELY"


def test_benchmark_metrics_are_deterministic_and_not_open_web_claim() -> None:
    first = evaluate_retrieval_benchmark(BENCHMARK, k=20)
    second = evaluate_retrieval_benchmark(BENCHMARK, k=20)
    for key in ("relevance_precision", "relevance_recall", "precision_at_k", "recall_at_k", "critical_positive_recall", "false_critical_count"):
        assert first[key] == second[key]
    assert first["metric_scope"] == "offline_frozen_benchmark_not_open_web_recall"


def test_benchmark_hard_gates() -> None:
    metrics = evaluate_retrieval_benchmark(BENCHMARK, k=20)
    assert_hard_retrieval_gates(metrics)


def test_runtime_metrics_expose_required_dimensions(tmp_path: Path) -> None:
    context = _context(tmp_path)
    request = query_portfolio_for_source(_sources()["arxiv"])[0]
    attempt = context.begin_query_attempt("arxiv", request)
    context.finish_query_attempt(attempt, status="success", raw_candidates=1)
    occurrence = context.record_raw_occurrence("arxiv", attempt, raw_title="LWE", abstract_present=True)
    record = make_paper_record(title="LWE", abstract="LWE cryptography", source="arxiv", source_url="https://arxiv.org/abs/x")
    context.record_normalized_candidate(occurrence, record)
    payload = build_candidate_ledger(
        [record], [record], [record], [record], [record], [record], [{"source": "arxiv", "health_status": "green"}],
        date(2026, 8, 11), context.query_attempts, run_id=context.run_id, raw_occurrences=context.raw_occurrences,
        normalized_candidates=context.normalized_candidates, route_events=context.route_events,
    )
    metrics = payload["runtime_metrics"]
    assert metrics["attempts_by_source"] == {"arxiv": 1}
    assert metrics["raw_occurrences_by_source"] == {"arxiv": 1}
    assert metrics["normalized_candidates_by_source"] == {"arxiv": 1}
    assert metrics["unique_canonical_candidates"] == 1


def test_normalization_failure_is_terminal(tmp_path: Path) -> None:
    context = _context(tmp_path)
    request = query_portfolio_for_source(_sources()["arxiv"])[0]
    attempt = context.begin_query_attempt("arxiv", request)
    occurrence = context.record_raw_occurrence("arxiv", attempt, raw_title="invalid")
    context.record_normalized_candidate(occurrence, None, status="NORMALIZATION_FAILED", reason="invalid identifier")
    event = context.route_events[-1]
    assert event["decision"] == "NORMALIZATION_FAILED"
    assert event["terminal"] is True


def test_occurrence_lifecycle_reaches_final_route(tmp_path: Path) -> None:
    context = _context(tmp_path)
    request = query_portfolio_for_source(_sources()["arxiv"])[0]
    attempt = context.begin_query_attempt("arxiv", request)
    occurrence = context.record_raw_occurrence("arxiv", attempt, raw_title="LWE Cryptanalysis", abstract_present=True)
    record = make_paper_record(
        title="LWE Cryptanalysis", abstract="A lattice cryptanalysis result for LWE.", source="arxiv",
        source_url="https://arxiv.org/abs/2608.99", arxiv_id="2608.99", relevance_label="A", relevance_score=90,
    )
    context.record_normalized_candidate(occurrence, record)
    payload = build_candidate_ledger(
        [record], [record], [record], [record], [record], [record], [{"source": "arxiv", "health_status": "green"}],
        date(2026, 8, 11), context.query_attempts, run_id=context.run_id, raw_occurrences=context.raw_occurrences,
        normalized_candidates=context.normalized_candidates, route_events=context.route_events,
    )
    lifecycle = payload["occurrence_lifecycles"][0]
    assert lifecycle["query_id"] == request.query_id
    assert lifecycle["normalization_status"] == "NORMALIZED"
    assert lifecycle["canonical_candidate_id"].startswith("canonical-")
    assert lifecycle["terminal_state"] == "FINAL_INCLUDED"
    assert payload["traceability"]["percentage"] == 100.0


def test_adapter_filtered_occurrence_is_explicit_not_untraced(tmp_path: Path) -> None:
    context = _context(tmp_path)
    request = query_portfolio_for_source(_sources()["arxiv"])[0]
    attempt = context.begin_query_attempt("arxiv", request)
    occurrence = context.record_raw_occurrence("arxiv", attempt, raw_title="Old LWE", abstract_present=True)
    record = make_paper_record(title="Old LWE", abstract="LWE", source="arxiv", source_url="https://arxiv.org/abs/old")
    context.record_normalized_candidate(occurrence, record)
    payload = build_candidate_ledger(
        [], [], [], [], [], [], [], date(2026, 8, 11), context.query_attempts, run_id=context.run_id,
        raw_occurrences=context.raw_occurrences, normalized_candidates=context.normalized_candidates,
        route_events=context.route_events,
    )
    assert payload["occurrence_lifecycles"][0]["terminal_state"] == "ADAPTER_FILTERED_BEFORE_CENTRAL_PIPELINE"
    assert payload["traceability"]["percentage"] == 100.0


def test_crossref_low_evidence_standalone_record_is_role_rejected(tmp_path: Path) -> None:
    context = FetchContext(tmp_path, datetime(2026, 8, 11, tzinfo=timezone.utc), False)
    for config in _sources().values():
        context.register_source(config)
    record = make_paper_record(
        title="Lattice Security Survey", source="crossref", source_url="https://doi.org/10.1/low",
        relevance_label="B", relevance_score=65,
    )
    kept, dropped = _filter_by_source_role([record], list(_sources().values()), context)
    assert kept == []
    assert dropped == [record]
    assert context.route_events[-1]["decision"] == "LOW_EVIDENCE_ENRICHMENT_ONLY_REJECTED"


def test_crossref_strong_title_record_can_still_contribute(tmp_path: Path) -> None:
    context = FetchContext(tmp_path, datetime(2026, 8, 11, tzinfo=timezone.utc), False)
    for config in _sources().values():
        context.register_source(config)
    record = make_paper_record(
        title="Direct ML-KEM Cryptanalysis", source="crossref", source_url="https://doi.org/10.1/strong",
        doi="10.1/strong", relevance_label="A", relevance_score=90,
    )
    kept, dropped = _filter_by_source_role([record], list(_sources().values()), context)
    assert kept == [record]
    assert dropped == []
    assert kept[0].doi == "10.1/strong"


def test_crossref_abstract_rich_record_can_still_contribute(tmp_path: Path) -> None:
    context = FetchContext(tmp_path, datetime(2026, 8, 11, tzinfo=timezone.utc), False)
    for config in _sources().values():
        context.register_source(config)
    record = make_paper_record(
        title="LWE Analysis", abstract="Detailed LWE cryptanalysis evidence.", source="crossref",
        source_url="https://doi.org/10.1/abstract", relevance_label="B", relevance_score=65,
    )
    kept, dropped = _filter_by_source_role([record], list(_sources().values()), context)
    assert kept == [record]
    assert dropped == []


def test_dblp_missing_abstract_is_title_only_evidence(tmp_path: Path) -> None:
    context = FetchContext(tmp_path, datetime(2026, 8, 11, tzinfo=timezone.utc), False)
    context.register_source(_sources()["dblp"])
    request = query_portfolio_for_source(_sources()["dblp"])[0]
    attempt = context.begin_query_attempt("dblp", request)
    occurrence = context.record_raw_occurrence("dblp", attempt, raw_title="LWE Paper", abstract_present=False)
    record = make_paper_record(title="LWE Paper", source="dblp", source_url="https://dblp.org/x")
    context.record_normalized_candidate(occurrence, record)
    assert context.normalized_candidates[0]["evidence_availability"] == "TITLE_ONLY"
    assert context.route_events[-1]["decision"] == "NO_ABSTRACT"
    assert context.route_events[-1]["terminal"] is False


def test_multi_source_canonical_provenance_is_preserved(tmp_path: Path) -> None:
    context = FetchContext(tmp_path, datetime(2026, 8, 11, tzinfo=timezone.utc), False)
    sources = _sources()
    for source in ("arxiv", "crossref"):
        context.register_source(sources[source])
    records = [
        make_paper_record(title="Shared LWE Paper", abstract="LWE", source="arxiv", source_url="https://arxiv.org/abs/x", doi="10.1/shared"),
        make_paper_record(title="Shared LWE Paper", source="crossref", source_url="https://doi.org/10.1/shared", doi="10.1/shared"),
    ]
    for record in records:
        request = query_portfolio_for_source(sources[record.source])[0]
        attempt = context.begin_query_attempt(record.source, request)
        occurrence = context.record_raw_occurrence(record.source, attempt, raw_title=record.title, abstract_present=bool(record.abstract))
        context.record_normalized_candidate(occurrence, record)
    canonical = deduplicate(records)
    payload = build_candidate_ledger(
        records, records, records, records, canonical, canonical, [], date(2026, 8, 11), context.query_attempts,
        run_id=context.run_id, raw_occurrences=context.raw_occurrences, normalized_candidates=context.normalized_candidates,
        route_events=context.route_events,
    )
    provenance = payload["canonical_candidates"][0]
    assert provenance["source_families"] == ["arxiv", "crossref"]
    assert len(provenance["query_attempt_ids"]) == 2
    assert len(provenance["raw_occurrence_ids"]) == 2
    assert provenance["strongest_evidence_provenance"] == "arxiv"


def test_benchmark_negative_controls_remain_noncritical() -> None:
    metrics = evaluate_retrieval_benchmark(BENCHMARK, k=20)
    for category in (
        "generic_quantum_negative", "generic_ai_negative", "generic_cybersecurity_negative",
        "strong_venue_irrelevant_negative",
    ):
        assert metrics["category_confusion"][category]["predicted_critical"] == 0


def test_runtime_metrics_expose_health_adjusted_unknown_coverage(tmp_path: Path) -> None:
    context = _context(tmp_path)
    request = query_portfolio_for_source(_sources()["arxiv"])[0]
    attempt = context.begin_query_attempt("arxiv", request)
    context.finish_query_attempt(attempt, status="rate_limited", raw_candidates=None, error_category="rate_limit")
    payload = build_candidate_ledger(
        [], [], [], [], [], [], [{"source": "arxiv", "health_status": "red"}], date(2026, 8, 11),
        context.query_attempts, run_id=context.run_id, raw_occurrences=context.raw_occurrences,
        normalized_candidates=context.normalized_candidates, route_events=context.route_events,
    )
    assert payload["runtime_metrics"]["source_health_adjusted_yield"] == {}
    assert payload["query_attempts"][0]["coverage_semantics"] == "UNKNOWN_COVERAGE"
