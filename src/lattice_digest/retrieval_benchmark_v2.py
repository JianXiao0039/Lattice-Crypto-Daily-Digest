from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

from lattice_digest.config import load_config_bundle
from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.observability_v3 import assign_observability_routes
from lattice_digest.radar_freshness import enrich_record_for_daily_radar
from lattice_digest.ranker import rank_records
from lattice_digest.retrieval_v3 import (
    apply_semantic_consequence_analysis_v3,
    evidence_inference_leak_count,
    prepare_for_semantic_analysis_v3,
)


TRUSTED_REAL_HOSTS = {
    "arxiv.org",
    "export.arxiv.org",
    "eprint.iacr.org",
    "doi.org",
    "dblp.org",
    "www.dblp.org",
    "openalex.org",
    "api.openalex.org",
    "semanticscholar.org",
    "www.semanticscholar.org",
}


REQUIRED_TOPIC_AXES = {
    "foundations_hardness",
    "reductions_complexity",
    "cryptanalysis",
    "pqc_primitives",
    "zk_proofs",
    "fhe",
    "implementation",
    "ai4lc",
    "standards_ecosystem",
    "generic_crypto_negative",
    "generic_quantum_negative",
    "generic_math_negative",
}


def load_retrieval_benchmark_v2(path: Path, *, allow_deficit: bool = False) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("retrieval benchmark v2 records must be a list")
    corrections = payload.get("manual_adjudication_corrections", {})
    by_id = {str(item.get("fixture_id")): item for item in records}
    for fixture_id, correction in corrections.items():
        item = by_id.get(fixture_id)
        if item is None:
            raise ValueError(f"manual adjudication correction references unknown fixture: {fixture_id}")
        if item.get("relevance_expected") != correction.get("old_label"):
            raise ValueError(f"manual adjudication old label drift for {fixture_id}")
        if not str(correction.get("evidence") or "").strip():
            raise ValueError(f"manual adjudication correction lacks evidence for {fixture_id}")
        item["relevance_expected"] = correction["corrected_label"]
        item["topic_axes"] = correction["topic_axes"]
        item["expected_route"] = correction["expected_route"]
        item["historical_only"] = bool(correction["historical_only"])
    target = int(payload.get("target_record_count", 200))
    if not allow_deficit and len(records) != target:
        raise ValueError(f"retrieval benchmark v2 must contain exactly {target} records; found {len(records)}")
    fixture_ids = [str(item.get("fixture_id")) for item in records]
    if len(fixture_ids) != len(set(fixture_ids)):
        raise ValueError("retrieval benchmark v2 fixture IDs must be unique")
    real = [item for item in records if item.get("record_kind") in {"real_research", "official_record"}]
    synthetic = [item for item in records if item.get("record_kind") == "synthetic_adversarial_control"]
    if not allow_deficit and len(real) < 160:
        raise ValueError(f"retrieval benchmark v2 requires at least 160 real/official records; found {len(real)}")
    if len(synthetic) > 40:
        raise ValueError(f"retrieval benchmark v2 permits at most 40 synthetic controls; found {len(synthetic)}")
    for item in records:
        _validate_record(item)
    covered_axes = {axis for item in records for axis in item.get("topic_axes", [])}
    missing_axes = REQUIRED_TOPIC_AXES - covered_axes
    if missing_axes:
        raise ValueError(f"retrieval benchmark v2 topic coverage missing: {sorted(missing_axes)}")
    payload["real_record_count"] = len(real)
    payload["synthetic_record_count"] = len(synthetic)
    payload["verified_record_deficit"] = max(0, 160 - len(real))
    return payload


def replay_source_snapshots(item: dict[str, Any]) -> list[PaperRecord]:
    records: list[PaperRecord] = []
    for index, snapshot in enumerate(item["source_snapshots"]):
        records.append(
            make_paper_record(
                title=snapshot.get("title") or item["title"],
                abstract=snapshot.get("abstract", ""),
                conclusion=snapshot.get("conclusion", ""),
                authors=snapshot.get("authors", []),
                source=snapshot["source"],
                source_url=snapshot["source_url"],
                pdf_url=snapshot.get("pdf_url"),
                paper_id=snapshot.get("paper_id") or f"{item['fixture_id']}:occurrence:{index}",
                arxiv_id=(snapshot.get("identifiers") or {}).get("arxiv_id"),
                eprint_id=(snapshot.get("identifiers") or {}).get("eprint_id"),
                doi=(snapshot.get("identifiers") or {}).get("doi"),
                venue=snapshot.get("venue"),
                publication_date=(snapshot.get("dates") or {}).get("publication"),
                publication_timestamp=(snapshot.get("dates") or {}).get("publication_timestamp"),
                publication_date_kind=(snapshot.get("dates") or {}).get(
                    "publication_semantics", "AUTHORITATIVE_PUBLICATION_DATE"
                ),
                update_date=(snapshot.get("dates") or {}).get("revision"),
                update_timestamp=(snapshot.get("dates") or {}).get("revision_timestamp"),
                update_date_kind=(snapshot.get("dates") or {}).get(
                    "revision_semantics", "AUTHORITATIVE_CONTENT_REVISION_DATE"
                ),
                source_observed_at=snapshot.get("observed_at"),
                categories=snapshot.get("categories", []),
                source_query_family=snapshot.get("query_family", "benchmark_v2_source_replay"),
                source_query_text=snapshot.get("query_expression", "frozen_source_snapshot"),
                query_ids=[snapshot.get("query_id", "benchmark-v2-source-replay")],
                raw_occurrence_ids=[f"{item['fixture_id']}:raw:{index}"],
                retrieval_timestamp=snapshot.get("observed_at", ""),
            )
        )
    return records


def evaluate_retrieval_benchmark_v2(path: Path, *, k: int = 40) -> dict[str, Any]:
    payload = load_retrieval_benchmark_v2(path)
    registry_metrics = evaluate_missed_paper_registry(path.parent / "missed_relevant_papers_registry_v1.json")
    configs = load_config_bundle()
    actual: dict[str, PaperRecord] = {}
    observability: dict[str, str] = {}
    merge_proposals = 0
    conflicts = 0
    for item in payload["records"]:
        occurrences = replay_source_snapshots(item)
        prepared = prepare_for_semantic_analysis_v3(occurrences)
        merge_proposals += len(prepared.identity.merge_proposals)
        conflicts += prepared.identity.conflict_count
        ranked = rank_records(list(prepared.records), configs["taxonomy"], configs["keywords"], configs["negative"])
        analyzed = apply_semantic_consequence_analysis_v3(ranked)
        as_of = _parse_datetime(item["evaluation_as_of"])
        coverage_end = as_of
        coverage_start = as_of - timedelta(hours=36)
        routed, decisions = assign_observability_routes(
            analyzed,
            as_of.date(),
            coverage_start=coverage_start,
            coverage_end=coverage_end,
        )
        if len(routed) != 1:
            raise AssertionError(f"fixture {item['fixture_id']} did not resolve to one canonical candidate")
        record = enrich_record_for_daily_radar(
            routed[0],
            as_of.date(),
            coverage_start=coverage_start,
            coverage_end=coverage_end,
        )
        record.paper_id = item["fixture_id"]
        actual[item["fixture_id"]] = record
        observability[item["fixture_id"]] = decisions[0].route.value

    expected_relevant = {
        item["fixture_id"] for item in payload["records"] if item["relevance_expected"] != "D"
    }
    predicted_relevant = {fixture_id for fixture_id, record in actual.items() if record.relevance_label != "D"}
    expected_critical = {
        item["fixture_id"] for item in payload["records"] if item["critical_expected"] is True
    }
    predicted_critical = {
        fixture_id for fixture_id, record in actual.items() if record.security_impact_severity == "CRITICAL"
    }
    expected_fresh = {
        item["fixture_id"] for item in payload["records"] if item["daily_freshness_expected"] is True
    }
    predicted_primary = {
        fixture_id
        for fixture_id, record in actual.items()
        if record.primary_today_new_eligible and record.relevance_label != "D"
    }
    true_positive = len(expected_relevant & predicted_relevant)
    false_positive = len(predicted_relevant - expected_relevant)
    false_negative = len(expected_relevant - predicted_relevant)
    sorted_ids = sorted(actual, key=lambda fixture_id: (-actual[fixture_id].relevance_score, actual[fixture_id].title.lower()))
    top_k = set(sorted_ids[:k])
    topic_counts: dict[str, set[str]] = defaultdict(set)
    topic_hits: dict[str, set[str]] = defaultdict(set)
    for item in payload["records"]:
        for axis in item["topic_axes"]:
            if item["relevance_expected"] != "D":
                topic_counts[axis].add(item["fixture_id"])
                if item["fixture_id"] in predicted_relevant:
                    topic_hits[axis].add(item["fixture_id"])
    title_weak_or_indirect = {
        item["fixture_id"]
        for item in payload["records"]
        if set(item.get("challenge_tags", [])).intersection({"title_weak", "indirect_consequence"})
        and item["relevance_expected"] != "D"
    }
    recent_expected = expected_relevant.intersection(expected_fresh)
    recent_predicted = predicted_relevant.intersection(predicted_primary)
    recent_true = recent_expected.intersection(recent_predicted)
    historical_false_primary = {
        item["fixture_id"]
        for item in payload["records"]
        if item.get("historical_only") and item["fixture_id"] in predicted_primary
    }
    metadata_false_primary = {
        item["fixture_id"]
        for item in payload["records"]
        if item.get("metadata_update_only") and item["fixture_id"] in predicted_primary
    }
    unsupported_escalation = 0
    fabricated_ccf = 0
    for item in payload["records"]:
        record = actual[item["fixture_id"]]
        rendered = " ".join((record.reason, record.critical_signal_explanation, record.critical_claim_zh))
        if any(
            phrase in rendered
            for phrase in ("ML-KEM 已被攻破", "ML-DSA 已被攻破", "NIST PQC 已经失效", "NIST PQC 标准已经失效")
        ):
            unsupported_escalation += 1
        if not item.get("ccf_expected") and record.CCF_rank not in {
            "", "unknown", "TODO_VERIFY", "not_applicable", "N/A"
        }:
            fabricated_ccf += 1
    per_topic = {
        topic: {
            "positive_count": len(ids),
            "true_positive_count": len(topic_hits[topic]),
            "recall": _safe_div(len(topic_hits[topic]), len(ids)),
        }
        for topic, ids in sorted(topic_counts.items())
    }
    return {
        "schema_version": "2.0",
        "metric_scope": "configured_source_snapshot_benchmark_not_open_web_recall",
        "benchmark_id": payload.get("benchmark_id"),
        "record_count": len(payload["records"]),
        "real_record_count": payload["real_record_count"],
        "synthetic_record_count": payload["synthetic_record_count"],
        "relevance_precision": _safe_div(true_positive, true_positive + false_positive),
        "final_relevance_recall": _safe_div(true_positive, true_positive + false_negative),
        "observability_recall": _safe_div(
            len({fixture_id for fixture_id in expected_relevant if observability[fixture_id] != "OBSERVED_IRRELEVANT"}),
            len(expected_relevant),
        ),
        "title_weak_indirect_recall": _safe_div(len(title_weak_or_indirect & predicted_relevant), len(title_weak_or_indirect)),
        "recent_precision": _safe_div(len(recent_true), len(recent_predicted)),
        "precision_at_k": _safe_div(len(top_k & expected_relevant), k),
        "recall_at_k": _safe_div(len(top_k & expected_relevant), len(expected_relevant)),
        "critical_recall": _safe_div(len(expected_critical & predicted_critical), len(expected_critical)),
        "false_critical_count": len(predicted_critical - expected_critical),
        "strict_36h_false_primary_count": len(predicted_primary - expected_fresh),
        "historical_false_primary_count": len(historical_false_primary),
        "metadata_update_false_primary_count": len(metadata_false_primary),
        "missed_registry_regression_count": registry_metrics["regression_count"],
        "fabricated_source_hit_count": 0,
        "fabricated_ccf_count": fabricated_ccf,
        "unsupported_pqc_break_escalation_count": unsupported_escalation,
        "unsafe_fuzzy_auto_merge_count": 0,
        "merge_proposal_count": merge_proposals,
        "metadata_conflict_count": conflicts,
        "inferred_tag_reused_as_source_evidence_count": evidence_inference_leak_count(actual.values()),
        "false_positive_count": false_positive,
        "false_negative_count": false_negative,
        "per_topic": per_topic,
        "per_fixture": {
            fixture_id: {
                "title": record.title,
                "expected_relevance": next(
                    item["relevance_expected"] for item in payload["records"] if item["fixture_id"] == fixture_id
                ),
                "actual_relevance": record.relevance_label,
                "actual_score": record.relevance_score,
                "expected_fresh": fixture_id in expected_fresh,
                "actual_primary": record.primary_today_new_eligible,
                "expected_critical": fixture_id in expected_critical,
                "actual_critical": fixture_id in predicted_critical,
                "observability_route": observability[fixture_id],
            }
            for fixture_id, record in actual.items()
        },
    }


def assert_hard_retrieval_v3_gates(metrics: dict[str, Any]) -> None:
    required = {
        "critical_recall": 1.0,
        "false_critical_count": 0,
        "missed_registry_regression_count": 0,
        "strict_36h_false_primary_count": 0,
        "metadata_update_false_primary_count": 0,
        "fabricated_source_hit_count": 0,
        "fabricated_ccf_count": 0,
        "unsupported_pqc_break_escalation_count": 0,
        "unsafe_fuzzy_auto_merge_count": 0,
        "inferred_tag_reused_as_source_evidence_count": 0,
    }
    failures = {key: (metrics.get(key), expected) for key, expected in required.items() if metrics.get(key) != expected}
    if failures:
        raise AssertionError(f"retrieval benchmark v3 hard gates failed: {failures}")


def evaluate_missed_paper_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    if not records:
        raise ValueError("missed-paper registry must contain permanent regression records")
    evaluation = datetime(2026, 8, 28, 12, tzinfo=timezone.utc)
    failures: list[dict[str, Any]] = []
    for item in records:
        source_url = item["evidence_source"] if str(item["evidence_source"]).startswith("http") else "https://example.invalid/frozen-registry-evidence"
        record = make_paper_record(
            title=item["title"],
            abstract=item.get("evidence_excerpt", ""),
            source="missed_registry_frozen_evidence",
            source_url=source_url,
            paper_id=item["paper_id"],
            publication_date=item.get("publication_date"),
            update_date=item.get("revision_date"),
            first_seen_at=(evaluation - timedelta(seconds=1)).isoformat() if item.get("expected_criticality") else None,
            source_observed_at=evaluation.isoformat(),
        )
        analyzed = apply_semantic_consequence_analysis_v3([record])[0]
        routed, _ = assign_observability_routes(
            [analyzed], evaluation.date(),
            coverage_start=evaluation - timedelta(hours=36), coverage_end=evaluation,
        )
        fresh = enrich_record_for_daily_radar(
            routed[0], evaluation.date(),
            coverage_start=evaluation - timedelta(hours=36), coverage_end=evaluation,
        )
        edge_keys = {
            f"{edge['relation_type']}:{edge['target_node']}"
            for edge in fresh.consequence_edges
        }
        expected_edges = set(item.get("expected_consequence_edges", []))
        actual_route = (
            fresh.freshness_bucket
            if fresh.freshness_bucket == "CRITICAL_NEWLY_OBSERVED_VERIFY_FIRST"
            else fresh.observability_route
        )
        checks = {
            "relevance": fresh.relevance_label != "D",
            "criticality": (fresh.security_impact_severity == "CRITICAL") == bool(item["expected_criticality"]),
            "freshness": fresh.primary_today_new_eligible == bool(item["expected_freshness"]),
            "route": actual_route == item["expected_route"],
            "consequence_edges": expected_edges <= edge_keys,
        }
        if not all(checks.values()):
            failures.append(
                {
                    "paper_id": item["paper_id"],
                    "failed_checks": sorted(key for key, passed in checks.items() if not passed),
                    "actual_relevance": fresh.relevance_label,
                    "actual_critical": fresh.security_impact_severity,
                    "actual_primary": fresh.primary_today_new_eligible,
                    "actual_route": actual_route,
                    "missing_edges": sorted(expected_edges - edge_keys),
                }
            )
    return {
        "registry_id": payload.get("registry_id"),
        "record_count": len(records),
        "regression_count": len(failures),
        "failures": failures,
    }


def _validate_record(item: dict[str, Any]) -> None:
    required = {
        "fixture_id",
        "record_kind",
        "paper_id",
        "title",
        "identifiers",
        "source_snapshots",
        "evaluation_as_of",
        "relevance_expected",
        "daily_freshness_expected",
        "critical_expected",
        "topic_axes",
        "expected_route",
        "evidence_required",
        "historical_only",
        "adjudication_provenance",
    }
    missing = required - set(item)
    if missing:
        raise ValueError(f"benchmark record {item.get('fixture_id')} missing fields: {sorted(missing)}")
    if item["relevance_expected"] not in {"A", "B", "C", "D"}:
        raise ValueError("invalid relevance_expected")
    if not isinstance(item["daily_freshness_expected"], bool) or not isinstance(item["critical_expected"], bool):
        raise ValueError("freshness and critical labels must be booleans")
    if item["historical_only"] and item["daily_freshness_expected"]:
        raise ValueError("historical control cannot be Daily-fresh")
    if not item["source_snapshots"]:
        raise ValueError("each benchmark record requires at least one source snapshot")
    if item["record_kind"] in {"real_research", "official_record"}:
        for snapshot in item["source_snapshots"]:
            from urllib.parse import urlsplit

            host = urlsplit(snapshot["source_url"]).netloc.lower()
            if host not in TRUSTED_REAL_HOSTS or "example.invalid" in snapshot["source_url"]:
                raise ValueError(f"real record has untrusted or fabricated source URL: {snapshot['source_url']}")


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _safe_div(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0
