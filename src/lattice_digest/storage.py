from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from lattice_digest.digest import generate_markdown
from lattice_digest.dedup import dedup_keys
from lattice_digest.models import PaperRecord, record_to_dict


def write_json(
    records: list[PaperRecord],
    output_dir: Path,
    digest_date: date,
    source_health: list[dict[str, object]] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{digest_date.isoformat()}.json"
    payload = {
        "records": [record_to_dict(record) for record in records],
        "source_health": source_health or [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_markdown(
    records: list[PaperRecord],
    output_dir: Path,
    digest_date: date,
    filtered_count: int,
    source_health: list[dict[str, object]] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{digest_date.isoformat()}.md"
    path.write_text(generate_markdown(records, digest_date, filtered_count, source_health), encoding="utf-8")
    return path


def write_sqlite(records: list[PaperRecord], db_path: Path) -> Path:
    with sqlite3.connect(db_path) as conn:
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
    return db_path
