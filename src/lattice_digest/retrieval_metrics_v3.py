from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from lattice_digest.models import PaperRecord
from lattice_digest.source_roles import unique_marginal_recall


def query_marginal_yield(
    canonical_records: Iterable[PaperRecord],
) -> dict[str, dict[str, int]]:
    records = list(canonical_records)
    by_query: dict[str, set[str]] = defaultdict(set)
    relevant_by_query: dict[str, set[str]] = defaultdict(set)
    all_queries_by_candidate: dict[str, set[str]] = {}
    for record in records:
        candidate_id = record.paper_id or record.source_url
        queries = set(record.query_ids or ([record.source_query_family] if record.source_query_family else []))
        all_queries_by_candidate[candidate_id] = queries
        for query_id in queries:
            by_query[query_id].add(candidate_id)
            if record.relevance_label != "D":
                relevant_by_query[query_id].add(candidate_id)
    metrics: dict[str, dict[str, int]] = {}
    for query_id in sorted(by_query):
        unique = {
            candidate_id
            for candidate_id in by_query[query_id]
            if all_queries_by_candidate.get(candidate_id) == {query_id}
        }
        metrics[query_id] = {
            "canonical_yield": len(by_query[query_id]),
            "relevant_yield": len(relevant_by_query[query_id]),
            "unique_marginal_yield": len(unique),
        }
    return metrics


def source_diversity_metrics(records: Iterable[PaperRecord]) -> dict[str, dict[str, int | float]]:
    canonical_sources: dict[str, set[str]] = {}
    relevant: set[str] = set()
    for record in records:
        candidate_id = record.paper_id or record.source_url
        canonical_sources[candidate_id] = {item.strip() for item in record.source.split(",") if item.strip()}
        if record.relevance_label != "D":
            relevant.add(candidate_id)
    return unique_marginal_recall(canonical_sources, relevant)


def evidence_metrics(records: Iterable[PaperRecord]) -> dict[str, int | float | dict[str, int]]:
    records = list(records)
    abstract_count = sum(bool(record.abstract) for record in records)
    enrichment_events = [event for record in records for event in record.enrichment_events]
    statuses = Counter(str(event.get("status")) for event in enrichment_events)
    upgraded_candidates = sum(any(event.get("status") == "EVIDENCE_UPGRADED" for event in record.enrichment_events) for record in records)
    conflicts = sum(len(record.conflicting_metadata) for record in records)
    return {
        "candidate_count": len(records),
        "abstract_availability": abstract_count / len(records) if records else 0.0,
        "enrichment_status_counts": dict(sorted(statuses.items())),
        "evidence_upgrade_rate": upgraded_candidates / len(records) if records else 0.0,
        "metadata_conflict_count": conflicts,
        "unsafe_fuzzy_auto_merge_count": 0,
    }
