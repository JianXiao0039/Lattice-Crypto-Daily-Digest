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
    from lattice_digest.evidence_contract import propagate_source_health
    records = propagate_source_health(records, source_health or [])
    from lattice_digest.publication_events import attach_events, POLICY_VERSION as EVENT_POLICY
    from lattice_digest.promotion_history import load_promotion_history
    event_metadata={**(metadata or {}), 'target_date':digest_date.isoformat()}
    prior = event_metadata.pop('_publication_prior', None)
    if prior is None:
        prior,_=load_promotion_history(output_dir,digest_date)
    records=[enrich_record_for_daily_radar(record,digest_date) for record in records]
    records,ledger=attach_events(records,event_metadata,prior)
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
        # A retrieved paper is not automatically a research proposal.
        item['research_hooks'] = []
        item['advisor_questions'] = []
        item['research_idea_status'] = 'NO_ACTIONABLE_RESEARCH_IDEA_FROM_CURRENT_EVIDENCE'
        item['research_sections'] = [s for s in item['research_sections'] if s not in {'Idea Bank Candidates','Paper Plan Candidates'}]
        item['report_buckets'] = [s for s in item['report_buckets'] if s not in {'Idea Bank Candidates','Paper Plan Candidates'}]
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
    payload_metadata.pop('_publication_prior',None)
    payload_metadata['publication_policy_version']=EVENT_POLICY
    payload_metadata['selection_counts']=ledger['counts']
    payload_metadata.update(derive_authority(enriched_records, source_health, source_configs=source_configs))
    payload_metadata['selection_counts']=ledger['counts']
    payload_metadata.setdefault('semantic_qa', {'status': 'UNKNOWN'})
    payload_metadata.setdefault('structural_qa', {'status': 'NOT_RUN'})
    payload = {
        "publication_event_ledger":ledger,
        "publication_history_evidence":[{k:p.get(k) for k in (
            'doi','arxiv_id','eprint_id','source_url','paper_id','source_urls','abstract','publication_timestamp',
            'publication_date','update_timestamp','update_date','update_date_kind','publication_event_id',
            'critical_verification_events')} for p in prior],
        "metadata": payload_metadata,
        "records": enriched_records,
        "source_health": source_health or [],
        "warnings": warnings or [],
    }
    from lattice_digest.evidence_contract import quality_gate_report
    payload['metadata']['evidence_quality_gates'] = quality_gate_report(enriched_records)
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
    if metadata and metadata.get('recovery_requested_window'):
        from lattice_digest.config import project_root
        from lattice_digest.recovery_window import validate_recovery_metadata
        from lattice_digest.runtime_provenance import runtime_provenance, public_runtime_allowed
        validate_recovery_metadata(metadata, digest_date)
        current = runtime_provenance(project_root(), 'DAILY', verify_remote=True)
        if not public_runtime_allowed(current, public_automation=True):
            raise ValueError('exact recovery requires published runtime provenance')
        if (metadata.get('runtime_git_head') != current['runtime_git_head']
                or metadata.get('runtime_code_manifest_sha256') != current['runtime_code_manifest_sha256']):
            raise ValueError('exact recovery runtime provenance changed since collection')
        metadata = {**metadata, 'exact_window_qa': {'status': 'PASS'},
                    'runtime_qa': {'status': 'PASS', 'state': current['runtime_code_state']}}
        json_target = daily_data_path(digest_date, output_root / 'data')
        md_target = daily_digest_path(digest_date, output_root / 'digests')
        if not force and (json_target.exists() or md_target.exists()):
            raise FileExistsError('canonical pair already exists; explicit force required')
        # Materialize and QA a disposable pair before creating any canonical target directory.
        # Cross-day evidence remains the single canonical history, never the empty scratch tree.
        with tempfile.TemporaryDirectory(prefix='lattice-exact-recovery-') as scratch:
            _publish_daily_pair_locked(records, Path(scratch), digest_date, filtered_count,
                                       source_health, warnings, since_window, metadata,
                                       source_configs=source_configs, history_root=output_root, diagnostic_root=output_root)
    path = daily_data_path(digest_date, output_root / 'data')
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name('.' + path.stem + '.publication.lock')
    stream = lock.open('x', encoding='utf-8')
    try:
        with stream:
            return _publish_daily_pair_locked(records, output_root, digest_date, filtered_count, source_health, warnings, since_window, metadata, force=force, source_configs=source_configs)
    finally:
        lock.unlink()


def _publish_daily_pair_locked(records, output_root, digest_date, filtered_count=0, source_health=None, warnings=None, since_window='36h', metadata=None, *, force=False, source_configs=None, history_root=None, diagnostic_root=None):
    """Validate first, then replace with rollback on ordinary I/O failure.

    This is NOT crash-atomic across two paths. Generation and content hashes
    make interrupted promotion fail closed in readers. No background writer.
    """
    from lattice_digest.promotion_history import load_promotion_history, classify_event
    json_path = daily_data_path(digest_date, output_root / 'data')
    md_path = daily_digest_path(digest_date, output_root / 'digests')
    if not force and (json_path.exists() or md_path.exists()):
        raise FileExistsError('canonical pair already exists; explicit force required')
    from lattice_digest.evidence_contract import propagate_source_health
    records = propagate_source_health(records, source_health or [])
    prior,_ = load_promotion_history((history_root or output_root) / 'data', digest_date)
    payload = build_daily_payload(records, output_root / 'data', digest_date, source_health, warnings, since_window, {**(metadata or {}), '_publication_prior':prior}, source_configs=source_configs)
    generation = uuid4().hex
    payload['metadata']['generation_id'] = generation
    md = generate_markdown(records, digest_date, filtered_count, source_health, warnings, since_window, {**payload['metadata'], '_publication_payload':payload}, source_configs=source_configs)
    md += f'\n<!-- generation:{generation} -->\n'
    payload['metadata']['markdown_sha256'] = hashlib.sha256(md.encode('utf-8')).hexdigest()
    structural = isinstance(payload['records'], list) and md.startswith('# ') and payload['metadata']['target_date'] == digest_date.isoformat()
    payload['metadata']['structural_qa'] = {'status': 'PASS' if structural else 'FAIL'}
    qa = semantic_qa(payload, md, candidate=True, source_configs=source_configs)
    prior, history = load_promotion_history((history_root or output_root) / 'data', digest_date)
    cross_errors = []
    cross_details = []
    # Never silently repair an explicitly forged primary flag supplied by a caller.
    for index,record in enumerate(records):
        event,_ = classify_event(record.model_dump(),prior)
        if record.primary_today_new_eligible and event != 'NEW_DISTINCT_PAPER' and payload['records'][index].get('publication_event_type')!='primary_publication_events':
            cross_errors.append('cross_day_false_primary')
            cross_details.append({'issue_code':'cross_day_false_primary','record_index':index,'event':event})
    for index, row in enumerate(payload['records']):
        event, _ = classify_event(row, prior)
        if row.get('primary_today_new_eligible') and event != 'NEW_DISTINCT_PAPER' and row.get('publication_event_type')!='primary_publication_events':
            cross_errors.append('cross_day_false_primary')
            cross_details.append({'issue_code': 'cross_day_false_primary', 'record_index': index, 'event': event})
    payload['metadata']['cross_day_qa'] = {'status': 'FAIL' if cross_errors else 'PASS', 'issues': cross_errors, 'history': history}
    payload['metadata']['semantic_qa'] = {k: v for k, v in qa.items() if k != 'derived_authority'}
    if not structural or qa['status'] != 'PASS' or cross_errors:
        from lattice_digest.publication_diagnostics import reject_daily_candidate
        reject_daily_candidate(diagnostic_root or output_root, payload, md, structural, qa, cross_details)
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
        # Preserve the historical library; only upsert identities observed today.
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
