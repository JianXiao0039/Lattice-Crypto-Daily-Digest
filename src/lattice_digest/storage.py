from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from lattice_digest.digest import generate_markdown, record_intelligence, research_tags
from lattice_digest.digest_sections import assign_report_buckets, assign_research_sections
from lattice_digest.dedup import dedup_keys
from lattice_digest.artifact_paths import daily_data_path, daily_digest_path
from lattice_digest.models import PaperRecord, record_to_dict
from lattice_digest.ranking_explainability import build_ranking_explanation


def write_json(
    records: list[PaperRecord],
    output_dir: Path,
    digest_date: date,
    source_health: list[dict[str, object]] | None = None,
    warnings: list[str] | None = None,
    since_window: str = "36h",
    metadata: dict[str, object] | None = None,
) -> Path:
    path = daily_data_path(digest_date, output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    enriched_records = []
    for record in records:
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
        enriched_records.append(item)
    payload_metadata = {
        "target_date": digest_date.isoformat(),
        "run_date": digest_date.isoformat(),
        "since_window": since_window,
        "total_records": len(records),
        "source_health": source_health or [],
        "warnings": warnings or [],
        "query_profile": "lattice-crypto-daily-digest",
        "version": "0.1.0",
    }
    if metadata:
        payload_metadata.update(metadata)
    payload_metadata["target_date"] = str(payload_metadata.get("target_date") or digest_date.isoformat())
    payload_metadata["since_window"] = since_window
    payload_metadata["total_records"] = len(records)
    payload_metadata["source_health"] = source_health or []
    payload_metadata["warnings"] = warnings or []
    payload = {
        "metadata": payload_metadata,
        "records": enriched_records,
        "source_health": source_health or [],
        "warnings": warnings or [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_markdown(
    records: list[PaperRecord],
    output_dir: Path,
    digest_date: date,
    filtered_count: int,
    source_health: list[dict[str, object]] | None = None,
    warnings: list[str] | None = None,
    since_window: str = "36h",
    metadata: dict[str, object] | None = None,
) -> Path:
    path = daily_digest_path(digest_date, output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        generate_markdown(records, digest_date, filtered_count, source_health, warnings, since_window, metadata),
        encoding="utf-8",
    )
    return path


def write_sqlite(records: list[PaperRecord], db_path: Path) -> Path:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                paper_key TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                source_url TEXT NOT NULL,
                publication_date TEXT,
                relevance_label TEXT NOT NULL,
                relevance_score INTEGER NOT NULL,
                data_json TEXT NOT NULL
            )
            """
        )
        conn.execute("DELETE FROM papers")
        for record in records:
            keys = dedup_keys(record)
            paper_key = keys[0] if keys else record.source_url
            conn.execute(
                """
                INSERT INTO papers (
                    paper_key, title, source, source_url, publication_date,
                    relevance_label, relevance_score, data_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(paper_key) DO UPDATE SET
                    title=excluded.title,
                    source=excluded.source,
                    source_url=excluded.source_url,
                    publication_date=excluded.publication_date,
                    relevance_label=excluded.relevance_label,
                    relevance_score=excluded.relevance_score,
                    data_json=excluded.data_json
                """,
                (
                    paper_key,
                    record.title,
                    record.source,
                    record.source_url,
                    record.publication_date,
                    record.relevance_label,
                    record.relevance_score,
                    json.dumps(record_to_dict(record), ensure_ascii=False),
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return db_path
