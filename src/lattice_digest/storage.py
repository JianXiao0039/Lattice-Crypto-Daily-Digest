from __future__ import annotations

import json
import sqlite3
import hashlib
import os
import tempfile
from uuid import uuid4
from datetime import date
from pathlib import Path

from lattice_digest.digest import generate_markdown, record_intelligence, research_tags
from lattice_digest.digest_sections import assign_report_buckets, assign_research_sections
from lattice_digest.dedup import dedup_keys
from lattice_digest.artifact_paths import daily_data_path, daily_digest_path
from lattice_digest.models import PaperRecord, record_to_dict
from lattice_digest.radar_freshness import enrich_record_for_daily_radar
from lattice_digest.ranking_explainability import build_ranking_explanation
from lattice_digest.authority import derive_authority, semantic_qa


def build_daily_payload(
    records: list[PaperRecord],
    output_dir: Path,
    digest_date: date,
    source_health: list[dict[str, object]] | None = None,
    warnings: list[str] | None = None,
    since_window: str = "36h",
    metadata: dict[str, object] | None = None,
    *,
    source_configs: list[dict] | None = None,
) -> dict:
    enriched_records = []
    for record in records:
        record = enrich_record_for_daily_radar(record, digest_date)
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
    payload_metadata.update(derive_authority(enriched_records, source_health, source_configs=source_configs))
    payload_metadata.setdefault('semantic_qa', {'status': 'UNKNOWN'})
    payload_metadata.setdefault('structural_qa', {'status': 'NOT_RUN'})
    payload = {
        "metadata": payload_metadata,
        "records": enriched_records,
        "source_health": source_health or [],
        "warnings": warnings or [],
    }
    return payload


def write_json(records, output_dir, digest_date, source_health=None, warnings=None, since_window='36h', metadata=None):
    payload = build_daily_payload(records, output_dir, digest_date, source_health, warnings, since_window, metadata)
    payload['metadata']['publication_state'] = 'UNVERIFIED_CANDIDATE'
    payload['metadata']['quality_status'] = 'unverified_candidate'
    path = daily_data_path(digest_date, output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def publish_daily_pair(records, output_root, digest_date, filtered_count=0, source_health=None, warnings=None, since_window='36h', metadata=None, *, force=False, source_configs=None):
    path = daily_data_path(digest_date, output_root / 'data')
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name('.' + path.stem + '.publication.lock')
    stream = lock.open('x', encoding='utf-8')
    try:
        with stream:
            return _publish_daily_pair_locked(records, output_root, digest_date, filtered_count, source_health, warnings, since_window, metadata, force=force, source_configs=source_configs)
    finally:
        lock.unlink()


def _publish_daily_pair_locked(records, output_root, digest_date, filtered_count=0, source_health=None, warnings=None, since_window='36h', metadata=None, *, force=False, source_configs=None):
    """Validate first, then replace with rollback on ordinary I/O failure.

    This is NOT crash-atomic across two paths. Generation and content hashes
    make interrupted promotion fail closed in readers. No background writer.
    """
    from lattice_digest.promotion_history import load_promotion_history, classify_event
    json_path = daily_data_path(digest_date, output_root / 'data')
    md_path = daily_digest_path(digest_date, output_root / 'digests')
    if not force and (json_path.exists() or md_path.exists()):
        raise FileExistsError('canonical pair already exists; explicit force required')
    payload = build_daily_payload(records, output_root / 'data', digest_date, source_health, warnings, since_window, metadata, source_configs=source_configs)
    generation = uuid4().hex
    payload['metadata']['generation_id'] = generation
    md = generate_markdown(records, digest_date, filtered_count, source_health, warnings, since_window, payload['metadata'], source_configs=source_configs)
    md += f'\n<!-- generation:{generation} -->\n'
    payload['metadata']['markdown_sha256'] = hashlib.sha256(md.encode('utf-8')).hexdigest()
    structural = isinstance(payload['records'], list) and md.startswith('# ') and payload['metadata']['target_date'] == digest_date.isoformat()
    payload['metadata']['structural_qa'] = {'status': 'PASS' if structural else 'FAIL'}
    qa = semantic_qa(payload, md, candidate=True, source_configs=source_configs)
    prior, history = load_promotion_history(output_root / 'data', digest_date)
    cross_errors = []
    for row in payload['records']:
        event, _ = classify_event(row, prior)
        if row.get('primary_today_new_eligible') and event != 'NEW_DISTINCT_PAPER':
            cross_errors.append('cross_day_false_primary')
    payload['metadata']['cross_day_qa'] = {'status': 'FAIL' if cross_errors else 'PASS', 'issues': cross_errors, 'history': history}
    payload['metadata']['semantic_qa'] = {k: v for k, v in qa.items() if k != 'derived_authority'}
    if not structural or qa['status'] != 'PASS' or cross_errors:
        error_path = md_path.with_name(md_path.stem + '-error.md')
        error_path.parent.mkdir(parents=True, exist_ok=True)
        with error_path.open('a', encoding='utf-8') as stream:
            stream.write('\n\nCandidate publication rejected; previous canonical pair preserved.\n' + json.dumps({'structural': structural, 'semantic': qa, 'cross_day': cross_errors}, ensure_ascii=False, indent=2))
        raise ValueError('Daily publication QA failed')
    payload['metadata']['publication_state'] = 'QA_PASSED'
    contents = [json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8'), md.encode('utf-8')]
    paths = [json_path, md_path]
    backups = [p.read_bytes() if p.exists() else None for p in paths]
    temporary = []
    promoted = []
    try:
        for path, content in zip(paths, contents):
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix='.daily-candidate-', dir=path.parent)
            temporary.append(Path(name))
            with os.fdopen(fd, 'wb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        for index, (temp, path) in enumerate(zip(temporary, paths)):
            os.replace(temp, path)
            promoted.append(index)
    except OSError:
        for index in reversed(promoted):
            if backups[index] is None:
                paths[index].unlink(missing_ok=True)
            else:
                paths[index].write_bytes(backups[index])
        raise
    finally:
        for temp in temporary:
            temp.unlink(missing_ok=True)
    return json_path, md_path


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
