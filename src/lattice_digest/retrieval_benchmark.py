from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

from lattice_digest.config import load_config_bundle
from lattice_digest.models import make_paper_record
from lattice_digest.radar_freshness import enrich_record_for_daily_radar
from lattice_digest.ranker import rank_records


REQUIRED_CATEGORIES = {
    "lwe_rlwe_mlwe_positive",
    "sis_module_sis_positive",
    "lattice_reduction_positive",
    "cryptanalysis_positive",
    "sparse_lwe_positive",
    "pqc_standard_positive",
    "lattice_signature_ch_positive",
    "ai4lc_positive",
    "zk_lattice_positive",
    "fhe_lattice_he_positive",
    "indirect_quantum_lattice_positive",
    "critical_security_positive",
    "generic_quantum_negative",
    "generic_ai_negative",
    "generic_cybersecurity_negative",
    "strong_venue_irrelevant_negative",
    "ambiguous_boundary",
    "title_evidence_contrast",
}


def load_retrieval_benchmark(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != 100:
        raise ValueError("retrieval benchmark v1 must contain exactly 100 records")
    fixture_ids = [str(item.get("fixture_id")) for item in records]
    if len(set(fixture_ids)) != len(fixture_ids):
        raise ValueError("retrieval benchmark fixture IDs must be unique")
    categories = {str(item.get("primary_benchmark_category")) for item in records}
    if categories != REQUIRED_CATEGORIES:
        raise ValueError(f"retrieval benchmark categories differ: {sorted(categories ^ REQUIRED_CATEGORIES)}")
    return payload


def _safe_div(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate_retrieval_benchmark(path: Path, *, k: int = 20) -> dict[str, Any]:
    payload = load_retrieval_benchmark(path)
    configs = load_config_bundle()
    expected_by_id: dict[str, dict[str, Any]] = {}
    source_items = []
    for item in payload["records"]:
        expected_by_id[str(item["fixture_id"])] = item
        source_items.append(
            make_paper_record(
                title=item["title"],
                abstract=item.get("abstract", ""),
                conclusion=item.get("conclusion", ""),
                authors=item.get("authors", []),
                source=item.get("source", "offline_benchmark"),
                source_url=item.get("source_url", f"https://example.invalid/benchmark/{item['fixture_id']}"),
                paper_id=item["fixture_id"],
                publication_date=item.get("publication_date", "2026-08-11"),
                venue=item.get("venue"),
            )
        )
    ranked = rank_records(source_items, configs["taxonomy"], configs["keywords"], configs["negative"])
    run_date = str(payload.get("run_date") or "2026-08-12")
    from datetime import date

    enriched = [enrich_record_for_daily_radar(record, date.fromisoformat(run_date)) for record in ranked]
    actual_by_id = {str(record.paper_id): record for record in enriched}
    expected_positive = {fid for fid, item in expected_by_id.items() if item["expected"]["relevant"]}
    predicted_positive = {fid for fid, record in actual_by_id.items() if record.relevance_label != "D"}
    true_positive = len(expected_positive & predicted_positive)
    false_positive = len(predicted_positive - expected_positive)
    false_negative = len(expected_positive - predicted_positive)
    critical_positive_ids = {
        fid for fid, item in expected_by_id.items() if item["expected"].get("critical") is True
    }
    predicted_critical = {
        fid for fid, record in actual_by_id.items() if record.security_impact_severity == "CRITICAL"
    }
    sorted_records = sorted(enriched, key=lambda record: (-record.relevance_score, record.title.lower()))
    top_k_ids = [str(record.paper_id) for record in sorted_records[:k]]
    relevant_top_k = len(set(top_k_ids) & expected_positive)
    category_confusion: dict[str, dict[str, int]] = {}
    for category in REQUIRED_CATEGORIES:
        category_ids = {fid for fid, item in expected_by_id.items() if item["primary_benchmark_category"] == category}
        category_confusion[category] = {
            "count": len(category_ids),
            "predicted_relevant": len(category_ids & predicted_positive),
            "predicted_critical": len(category_ids & predicted_critical),
        }
    stale_to_primary = 0
    backfill_read_now = 0
    fabricated_ccf = 0
    unsupported_escalation = 0
    forbidden = ("ML-KEM 已被攻破", "ML-DSA 已被攻破", "NIST PQC 标准已经失效", "NIST PQC 已经失效")
    for fid, record in actual_by_id.items():
        expected = expected_by_id[fid]["expected"]
        if expected.get("route_class") == "backfill" and record.primary_today_new_eligible:
            stale_to_primary += 1
        if expected.get("route_class") == "backfill" and record.suggested_action in {"Read now", "READ_AND_VERIFY_IMMEDIATELY"}:
            backfill_read_now += 1
        if not expected.get("ccf_rank") and record.CCF_rank not in {"", "unknown", "TODO_VERIFY"}:
            fabricated_ccf += 1
        rendered = " ".join([record.reason, record.critical_signal_explanation, record.critical_claim_zh])
        if any(phrase in rendered for phrase in forbidden):
            unsupported_escalation += 1
    false_positive_classes = Counter(
        expected_by_id[fid]["primary_benchmark_category"] for fid in predicted_positive - expected_positive
    )
    false_negative_classes = Counter(
        expected_by_id[fid]["primary_benchmark_category"] for fid in expected_positive - predicted_positive
    )
    return {
        "schema_version": "1.0",
        "metric_scope": "offline_frozen_benchmark_not_open_web_recall",
        "benchmark_id": payload.get("benchmark_id"),
        "record_count": len(payload["records"]),
        "k": k,
        "relevance_precision": _safe_div(true_positive, true_positive + false_positive),
        "relevance_recall": _safe_div(true_positive, true_positive + false_negative),
        "precision_at_k": _safe_div(relevant_top_k, k),
        "recall_at_k": _safe_div(relevant_top_k, len(expected_positive)),
        "critical_positive_recall": _safe_div(len(critical_positive_ids & predicted_critical), len(critical_positive_ids)),
        "false_critical_count": len(predicted_critical - critical_positive_ids),
        "stale_to_primary_count": stale_to_primary,
        "backfill_to_read_now_count": backfill_read_now,
        "fabricated_ccf_count": fabricated_ccf,
        "unsupported_standardized_pqc_break_escalation_count": unsupported_escalation,
        "true_positive_count": true_positive,
        "false_positive_count": false_positive,
        "false_negative_count": false_negative,
        "category_confusion": category_confusion,
        "false_positive_classes": dict(sorted(false_positive_classes.items())),
        "false_negative_classes": dict(sorted(false_negative_classes.items())),
        "per_fixture": {
            fid: {
                "expected_relevant": expected_by_id[fid]["expected"]["relevant"],
                "actual_label": record.relevance_label,
                "actual_score": record.relevance_score,
                "actual_critical": record.security_impact_severity == "CRITICAL",
                "actual_impact": record.security_impact_severity,
                "actual_confidence": record.evidence_confidence,
                "actual_action": record.suggested_action,
                "actual_topic_tags": record.inferred_topic_tags,
            }
            for fid, record in actual_by_id.items()
        },
    }


def assert_hard_retrieval_gates(metrics: dict[str, Any]) -> None:
    required = {
        "critical_positive_recall": 1.0,
        "false_critical_count": 0,
        "stale_to_primary_count": 0,
        "backfill_to_read_now_count": 0,
        "fabricated_ccf_count": 0,
        "unsupported_standardized_pqc_break_escalation_count": 0,
    }
    failures = {key: (metrics.get(key), value) for key, value in required.items() if metrics.get(key) != value}
    if failures:
        raise AssertionError(f"retrieval benchmark hard gates failed: {failures}")
