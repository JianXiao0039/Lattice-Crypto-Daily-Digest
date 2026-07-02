from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Mapping

from lattice_digest.digest import generate_markdown, record_intelligence, research_tags
from lattice_digest.digest_sections import assign_report_buckets, assign_research_sections
from lattice_digest.models import PaperRecord, make_paper_record, record_to_dict
from lattice_digest.radar_freshness import enrich_record_for_daily_radar
from lattice_digest.ranking_explainability import build_ranking_explanation


_MODEL_FIELDS = set(PaperRecord.model_fields)


def _legacy_record_to_paper_record(record: Mapping[str, Any]) -> PaperRecord:
    data = {key: value for key, value in record.items() if key in _MODEL_FIELDS}
    data.setdefault("title", record.get("title_en") or record.get("title") or "unknown")
    data.setdefault("source", record.get("source") or record.get("publisher_or_source") or "unknown")
    data.setdefault("source_url", record.get("source_url") or record.get("url") or "")
    data.setdefault("abstract", record.get("abstract") or record.get("abstract_en") or "")
    data.setdefault("chinese_title", record.get("chinese_title") or record.get("title_zh") or data["title"])
    data.setdefault("authors", record.get("authors") or [])
    data.setdefault("taxonomy_tags", record.get("taxonomy_tags") or record.get("tags") or record.get("research_tags") or [])
    data.setdefault("keywords_matched", record.get("keywords_matched") or [])
    data.setdefault("negative_keywords_matched", record.get("negative_keywords_matched") or [])
    data.setdefault("relevance_label", record.get("relevance_label") or "D")
    data.setdefault("relevance_score", int(record.get("relevance_score") or record.get("recommendation_score") or 0))
    return make_paper_record(**data)


def normalize_daily_payload(payload: Mapping[str, Any], digest_date: date) -> dict[str, Any]:
    records = [_legacy_record_to_paper_record(record) for record in payload.get("records", [])]
    enriched = [enrich_record_for_daily_radar(record, digest_date) for record in records]
    normalized_records: list[dict[str, Any]] = []
    for record in enriched:
        item = record_to_dict(record)
        intelligence = record_intelligence(record)
        item.update(
            {
                "date": record.publication_date or record.update_date,
                "year": (record.publication_date or record.update_date or "")[:4] or None,
                "url": record.source_url,
                "tags": research_tags(record),
                "research_tags": research_tags(record),
                "priority": intelligence["priority"],
                "reading_priority_score": intelligence["reading_priority_score"],
                "priority_label": intelligence["priority_label"],
                "reason_for_priority": intelligence["reason_for_priority"],
                "why_it_matters": intelligence["why_it_matters"],
                "suggested_action": intelligence["suggested_action"],
                "research_hooks": intelligence["research_hooks"],
                "advisor_questions": intelligence["advisor_questions"],
                "source_health_ref": intelligence["source_health_ref"],
                "ranking_explanation": build_ranking_explanation(record),
                "research_sections": assign_research_sections(record),
                "report_buckets": assign_report_buckets(record),
            }
        )
        normalized_records.append(item)

    metadata = dict(payload.get("metadata", {}))
    metadata["target_date"] = str(metadata.get("target_date") or digest_date.isoformat())
    metadata["run_date"] = str(metadata.get("run_date") or digest_date.isoformat())
    metadata["total_records"] = len(normalized_records)
    metadata["legacy_daily_output_normalized"] = True
    metadata["legacy_daily_output_normalization_policy"] = "radar freshness/metadata contract v0.1"
    source_health = list(payload.get("source_health") or metadata.get("source_health") or [])
    warnings = list(payload.get("warnings") or metadata.get("warnings") or [])
    return {
        "metadata": metadata,
        "records": normalized_records,
        "source_health": source_health,
        "warnings": warnings,
    }


def normalize_daily_json_file(path: Path, digest_date: date) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    normalized = normalize_daily_payload(payload, digest_date)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return normalized


def render_normalized_daily_markdown(payload: Mapping[str, Any], digest_date: date) -> str:
    records = [_legacy_record_to_paper_record(record) for record in payload.get("records", [])]
    metadata = dict(payload.get("metadata", {}))
    source_health = list(payload.get("source_health") or metadata.get("source_health") or [])
    warnings = list(payload.get("warnings") or metadata.get("warnings") or [])
    since_window = str(metadata.get("since_window") or "36h")
    return generate_markdown(records, digest_date, 0, source_health, warnings, since_window, metadata)


def normalize_daily_markdown_file(json_path: Path, markdown_path: Path, digest_date: date) -> str:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = render_normalized_daily_markdown(payload, digest_date)
    markdown_path.write_text(markdown, encoding="utf-8")
    return markdown
