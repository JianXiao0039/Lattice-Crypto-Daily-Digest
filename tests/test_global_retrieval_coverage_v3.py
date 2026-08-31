from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from lattice_digest.consequence_graph_v3 import (
    ClaimStatus,
    ConsequenceEdge,
    ConsequenceGraph,
    EdgeEvidenceState,
    RelationType,
    extract_record_edges,
)
from lattice_digest.enrichment_v3 import (
    EnrichmentPayload,
    EnrichmentStatus,
    SelectiveEnrichmentCoordinator,
)
from lattice_digest.identity_v3 import resolve_identity_and_merge
from lattice_digest.models import make_paper_record
from lattice_digest.observability_v3 import ObservabilityRoute, assign_observability_routes
from lattice_digest.ontology_v3 import load_ontology_v3
from lattice_digest.query_portfolio_v3 import load_query_portfolio_v3
from lattice_digest.retrieval_benchmark_v2 import (
    assert_hard_retrieval_v3_gates,
    evaluate_missed_paper_registry,
    evaluate_retrieval_benchmark_v2,
    load_retrieval_benchmark_v2,
)
from lattice_digest.retrieval_v3 import apply_semantic_consequence_analysis_v3, evidence_inference_leak_count
from lattice_digest.source_roles import unique_marginal_recall


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "tests" / "fixtures" / "recent_paper_benchmark_v2.json"
REGISTRY = ROOT / "tests" / "fixtures" / "missed_relevant_papers_registry_v1.json"


def paper(title: str, abstract: str = "", **kwargs):
    return make_paper_record(
        title=title,
        abstract=abstract,
        source=kwargs.pop("source", "arxiv"),
        source_url=kwargs.pop("source_url", "https://arxiv.org/abs/2608.00001"),
        **kwargs,
    )


def analyze(title: str, abstract: str):
    return apply_semantic_consequence_analysis_v3([paper(title, abstract)])[0]


def test_ontology_v3_is_typed_relation_aware_and_separates_inference():
    ontology = load_ontology_v3()
    assert set(ontology.by_domain) == {
        "foundations_hardness", "reductions_complexity", "cryptanalysis", "pqc_primitives",
        "zk_proofs", "fhe", "implementation", "ai4lc", "standards_ecosystem",
    }
    assert len(ontology.document.concepts) >= 40
    for concept in ontology.document.concepts:
        assert set(concept.source_grounded_terms).isdisjoint(concept.inferred_tags)
        assert concept.evidence_policy


@pytest.mark.parametrize(
    ("title", "abstract", "target"),
    [
        ("A New Algebraic Method", "We prove hardness for principal cyclotomic ideal CVP.", "HARD.STRUCTURED_CVP"),
        ("Quaternion Reduction", "Quaternion BKZ improves attacks on MLIP instances relevant to HAWK.", "FND.MLIP"),
        ("Distributed Exact Proofs", "A threshold zero knowledge protocol for exact relations using Hint-MLWE.", "PROOF.THRESHOLD_ZK"),
        ("Anonymous Authorization", "A linkable ring signature from Module-SIS lattices.", "PRIM.PRIVACY_SIGNATURE"),
        ("Compact Signatures", "Iterative rejection sampling accelerates Fiat-Shamir lattice signatures.", "PRIM.LATTICE_SIGNATURE"),
        ("Post-Quantum Handshake", "An authenticated key exchange (AKE) construction from MLWE lattices.", "PRIM.AKE"),
    ],
)
def test_typed_consequence_classes_survive_title_weakness(title, abstract, target):
    record = analyze(title, abstract)
    assert record.relevance_label != "D"
    assert target in {edge["target_node"] for edge in record.consequence_edges}


def test_source_evidence_and_inference_are_distinct_namespaces():
    record = analyze("Efficient Quantum FHE", "Fully homomorphic encryption from LWE with bootstrapping.")
    assert all(tag.startswith("inferred:") for tag in record.inferred_topic_tags)
    assert evidence_inference_leak_count([record]) == 0


def test_critical_graph_requires_source_grounded_edges_and_is_bounded():
    with pytest.raises(ValueError, match="critical consequence edge"):
        ConsequenceEdge(
            source_node="paper:x",
            relation_type=RelationType.AFFECTS_SECURITY,
            target_node="FND.LWE",
            evidence_state=EdgeEvidenceState.INFERRED_HYPOTHESIS,
            evidence_source="model_inference",
            evidence_span="",
            source_url="",
            confidence=0.5,
            claim_status=ClaimStatus.MODEL_INFERENCE,
            critical_eligible=True,
        )
    edges = []
    for left, right in (("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")):
        edges.append(
            ConsequenceEdge(
                source_node=left,
                relation_type=RelationType.REDUCES_TO,
                target_node=right,
                evidence_state=EdgeEvidenceState.SOURCE_ASSERTED,
                evidence_source="abstract",
                evidence_span="source assertion",
                source_url="https://arxiv.org/abs/2608.1",
                confidence=0.9,
                critical_eligible=True,
            )
        )
    graph = ConsequenceGraph(edges)
    assert graph.paths_from({"a"}, {"d"}, critical=True)
    assert not graph.paths_from({"a"}, {"e"}, critical=True)
    assert not graph.paths_from({"a"}, {"d"}, critical=False)


def test_dcp_critical_requires_explicit_solved_target_and_lattice_consequence():
    generic = extract_record_edges(
        paper_node="paper:g",
        title="Quantum Algorithms for Average-Case Lattice Problems",
        abstract="We discuss DCP reductions and give a polynomial-time filtering algorithm.",
        conclusion="",
        source_url="https://arxiv.org/abs/2108.11015",
        source_concept_ids=(),
    )
    assert not any(edge.critical_eligible for edge in generic)
    canary = analyze(
        "A Polynomial-Time Quantum Algorithm for the Dihedral Coset Problem",
        "This preliminary draft claims a polynomial-time quantum algorithm for the Dihedral Coset Problem. "
        "Combined with Regev's reduction of lattice problems to DCP, it yields algorithms for SVP and LWE.",
    )
    assert canary.security_impact_severity == "CRITICAL"
    assert "standardized-PQC break" in canary.critical_signal_explanation


@pytest.mark.parametrize(
    ("title", "abstract"),
    [
        ("Fast Enumeration of Set Partitions", "A combinatorial enumeration algorithm without cryptography."),
        ("Crystal Lattice Defects", "Thermal conductivity in a crystal lattice material."),
        ("Quantum Walk Search", "A generic quantum algorithm with no cryptographic or lattice consequence."),
    ],
)
def test_generic_false_positive_controls_are_rejected(title, abstract):
    assert analyze(title, abstract).relevance_label == "D"


def test_missing_abstract_and_uncertain_date_remain_observable_not_daily():
    record = analyze("Module-LIP Reduction Study", "")
    assert record.relevance_label != "D"
    routed, decisions = assign_observability_routes([record], date(2026, 8, 28))
    assert routed[0].observability_route == ObservabilityRoute.OBSERVED_RELEVANT_DATE_UNCERTAIN
    assert decisions[0].daily_eligible is False


def test_historical_relevant_record_is_not_daily_filler():
    record = analyze("Learning With Errors", "A lattice cryptography study of LWE.")
    record.publication_date = "2020-01-01"
    end = datetime(2026, 8, 28, 12, tzinfo=timezone.utc)
    routed, decisions = assign_observability_routes(
        [record], end.date(), coverage_start=end - timedelta(hours=36), coverage_end=end
    )
    assert routed[0].observability_route == ObservabilityRoute.OBSERVED_RELEVANT_STALE
    assert not decisions[0].daily_eligible


def test_identity_merge_preserves_all_evidence_and_version_relation():
    left = paper(
        "An LWE Construction",
        "short",
        arxiv_id="2608.00001v1",
        paper_id="arxiv:2608.00001v1",
        authors=["Alice Example"],
        query_ids=["q1"],
        raw_occurrence_ids=["raw1"],
        publication_date="2026-08-27",
    )
    right = paper(
        "An LWE Construction",
        "A much longer official abstract about Learning With Errors.",
        source="crossref",
        source_url="https://doi.org/10.1000/lwe",
        doi="10.1000/lwe",
        arxiv_id="2608.00001v2",
        paper_id="doi:10.1000/lwe",
        authors=["Alice Example"],
        query_ids=["q2"],
        raw_occurrence_ids=["raw2"],
        publication_date="2026-08-28",
    )
    result = resolve_identity_and_merge([left, right])
    assert len(result.canonical_records) == 1
    merged = result.canonical_records[0]
    assert set(merged.query_ids) >= {"q1", "q2"}
    assert set(merged.raw_occurrence_ids) == {"raw1", "raw2"}
    assert len(merged.source_urls) == 2
    assert merged.version_relations
    assert "much longer" in merged.abstract


def test_fuzzy_title_alone_creates_proposal_not_auto_merge():
    result = resolve_identity_and_merge(
        [
            paper("Module LWE Signatures with Compact Proofs", authors=["Alice"]),
            paper(
                "Module-LWE Signatures with Compact Proof",
                authors=["Bob"],
                source_url="https://arxiv.org/abs/2608.99999",
            ),
        ]
    )
    assert len(result.canonical_records) == 2
    assert result.merge_proposals
    assert result.strong_merge_count == 0


def test_selective_enrichment_upgrades_missing_abstract_without_global_fetch():
    class Provider:
        name = "fixture_provider"

        def enrich(self, record, request):
            return EnrichmentPayload(
                source=self.name,
                source_url=record.source_url,
                status=EnrichmentStatus.EVIDENCE_UPGRADED,
                fields={"abstract": "Module-LWE source-supported abstract."},
            )

    result = SelectiveEnrichmentCoordinator([Provider()], max_candidates=1, max_requests=1).run(
        [paper("An Algebraic Construction")]
    )
    assert result.request_count == 1
    assert result.upgraded_count == 1
    assert result.records[0].abstract.startswith("Module-LWE")
    assert result.events[0].content_hash


def test_query_portfolio_is_shadow_bounded_and_family_fair():
    portfolio = load_query_portfolio_v3()
    assert not portfolio.production_active
    compiled = portfolio.compile_for_sources(["arxiv", "openalex", "crossref", "dblp", "semantic_scholar", "iacr_eprint"])
    assert len({query.family_id for query in compiled}) >= 15
    scheduled = portfolio.fair_schedule(
        ["arxiv", "openalex", "crossref", "dblp", "semantic_scholar", "iacr_eprint"],
        global_budget=30,
        per_source_budget=8,
    )
    assert len(scheduled) <= 30
    assert all(sum(query.source == source for query in scheduled) <= 8 for source in {q.source for q in scheduled})
    assert len({query.family_id for query in scheduled}) >= 12


def test_unique_source_marginal_recall_is_not_configured_source_count():
    metrics = unique_marginal_recall(
        {
            "p1": {"arxiv", "openalex"},
            "p2": {"arxiv", "openalex", "crossref"},
            "p3": {"crossref"},
        },
        {"p1", "p2", "p3"},
    )
    assert len(metrics) == 3
    assert metrics["crossref"]["unique_relevant_contribution"] == 1
    assert metrics["arxiv"]["unique_relevant_contribution"] == 0
    assert metrics["openalex"]["unique_relevant_contribution"] == 0


def test_missed_paper_registry_is_permanent_and_historical_controls_stay_stale():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    records = payload["records"]
    assert len(records) >= 10
    assert len({item["paper_id"] for item in records}) == len(records)
    required = {
        "paper_id", "title", "identifier", "publication_date", "revision_date", "evidence_source",
        "research_axes", "missed_pipeline_stage", "root_cause", "expected_relevance",
        "expected_criticality", "expected_freshness", "expected_route", "historical_only",
        "regression_status", "reported_at", "expected_consequence_edges", "repair_history",
        "last_verified_commit",
    }
    assert all(required <= set(item) for item in records)
    assert all(not item["expected_freshness"] for item in records if item["historical_only"])
    metrics = evaluate_missed_paper_registry(REGISTRY)
    assert metrics["regression_count"] == 0, metrics["failures"]


def test_recent_paper_benchmark_v2_schema_and_hard_gates():
    payload = load_retrieval_benchmark_v2(BENCHMARK)
    assert payload["real_record_count"] == 160
    assert payload["synthetic_record_count"] == 40
    assert payload["verified_record_deficit"] == 0
    metrics = evaluate_retrieval_benchmark_v2(BENCHMARK)
    assert_hard_retrieval_v3_gates(metrics)
    assert metrics["observability_recall"] >= 0.97
    assert metrics["final_relevance_recall"] >= 0.95
    assert metrics["title_weak_indirect_recall"] >= 0.95
    assert metrics["recent_precision"] >= 0.85
