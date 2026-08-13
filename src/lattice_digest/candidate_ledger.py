from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from lattice_digest.models import PaperRecord


def candidate_id(record: PaperRecord) -> str:
    stable = "|".join(
        [record.source, record.paper_id or record.source_url or "", record.normalized_title or record.title.lower()]
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:24]


def build_candidate_ledger(
    collected: list[PaperRecord],
    ranked: list[PaperRecord],
    coverage_kept: list[PaperRecord],
    reliable: list[PaperRecord],
    deduped: list[PaperRecord],
    final_records: list[PaperRecord],
    source_health: list[dict[str, object]],
    target_date: date,
    query_attempts: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    ranked_by_id = {candidate_id(record): record for record in ranked}
    coverage_ids = {candidate_id(record) for record in coverage_kept}
    reliable_ids = {candidate_id(record) for record in reliable}
    deduped_ids = {candidate_id(record) for record in deduped}
    final_ids = {candidate_id(record) for record in final_records}
    health_by_source = {
        str(item.get("source")): str(item.get("health_status") or item.get("status") or "unknown")
        for item in source_health
    }
    rows: list[dict[str, object]] = []
    for raw in collected:
        cid = candidate_id(raw)
        record = ranked_by_id.get(cid, raw)
        drop_stage = None
        drop_reason = None
        final_route = "included"
        if not record.title or not record.source or not record.source_url:
            drop_stage, drop_reason, final_route = "NORMALIZATION", "missing required title/source/source_url", "dropped"
        elif cid not in coverage_ids:
            drop_stage, drop_reason, final_route = "FRESHNESS", "outside selected coverage window", "dropped"
        elif record.relevance_label == "D" or cid not in reliable_ids:
            drop_stage, drop_reason, final_route = "RELEVANCE", record.reason or "D classification", "dropped"
        elif cid not in deduped_ids:
            drop_stage, drop_reason, final_route = "ROUTE", "deduplicated into another canonical record", "merged"
        elif cid not in final_ids:
            drop_stage, drop_reason, final_route = "ROUTE", "not routed to final digest", "dropped"
        rows.append(
            {
                "candidate_id": cid,
                "source_family": record.source,
                "query_family": record.source_query_family or "source_native_feed_or_legacy_query",
                "query_text": record.source_query_text or "not_recorded",
                "retrieval_timestamp": record.retrieval_timestamp or "unknown",
                "source_health": health_by_source.get(record.source, record.source_health or "unknown"),
                "raw_title": raw.title,
                "normalized_title": record.normalized_title,
                "identifier": record.paper_id or record.arxiv_id or record.eprint_id or record.doi or record.source_url,
                "publication_date": record.publication_date,
                "update_date": record.update_date,
                "abstract_present": bool(record.abstract),
                "normalization_status": "normalized" if record.normalized_title else "incomplete",
                "pre_relevance_status": "candidate",
                "post_relevance_status": f"{record.relevance_label}:{record.relevance_score}",
                "security_impact_severity": record.security_impact_severity,
                "drop_stage": drop_stage,
                "drop_reason": drop_reason,
                "final_route": final_route,
            }
        )
    return {
        "schema_version": "1.0",
        "artifact_role": "scratch_diagnostic_non_authoritative",
        "target_date": target_date.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diagnostic_chain": ["SOURCE", "QUERY", "NORMALIZATION", "RELEVANCE", "FRESHNESS", "ROUTE"],
        "source_health": source_health,
        "query_attempts": query_attempts or [],
        "candidates": rows,
    }


def write_candidate_ledger(payload: dict[str, object], output_root: Path, target_date: date) -> Path:
    output_dir = output_root / "audits" / "worktree"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"candidate-retrieval-ledger-{target_date.isoformat()}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
