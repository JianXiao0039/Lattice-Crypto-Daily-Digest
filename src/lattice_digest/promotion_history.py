"""Bounded, canonical-only publication history. Titles never establish identity."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from lattice_digest.artifact_paths import daily_data_path
from lattice_digest.models import PaperRecord

HISTORY_DAYS = 14
MAX_HISTORY_BYTES = 16 * 1024 * 1024
MAX_HISTORY_RECORDS = 10000
EVENTS = {
    'UNCHANGED_CROSS_DAY_DUPLICATE', 'GENUINE_NEW_VERSION',
    'GENUINE_CONTENT_REVISION', 'METADATA_ONLY_UPDATE',
    'NEW_DISTINCT_PAPER', 'IDENTITY_UNCERTAIN',
}


def identity_keys(record: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for field, prefix in [('doi', 'doi'), ('arxiv_id', 'arxiv'), ('eprint_id', 'eprint')]:
        value = str(record.get(field) or '').strip().lower()
        value = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', value)
        if value:
            keys.add(prefix + ':' + (re.sub(r'v\d+$', '', value) if prefix == 'arxiv' else value))
    for value in [record.get('source_url'), record.get('paper_id'), *(record.get('source_urls') or [])]:
        text = str(value or '').strip().lower()
        arxiv = re.search(r'(?:arxiv:|arxiv\.org/(?:abs|pdf)/)(\d{4}\.\d{4,5}|[a-z.-]+/\d{7})(?:v\d+)?', text)
        eprint = re.search(r'(?:eprint:|eprint\.iacr\.org/)(\d{4}/\d+)', text)
        if arxiv:
            keys.add('arxiv:' + arxiv[1])
        elif eprint:
            keys.add('eprint:' + eprint[1])
        elif text.startswith(('http://', 'https://')):
            keys.add('url:' + re.sub(r'^http:', 'https:', text).rstrip('/'))
    return keys


def authoritative_version(record: dict[str, Any]) -> str:
    versions = set()
    for value in [record.get('arxiv_id'), record.get('source_url'), record.get('paper_id')]:
        match = re.search(r'(?:\d{4}\.\d{4,5}|/\d{7})(v\d+)(?:[?#/]|$)', str(value or ''))
        if match:
            versions.add(match[1])
    return next(iter(versions)) if len(versions) == 1 else ''


def content_fingerprint(record: dict[str, Any]) -> str:
    # Compare source content, excluding mutable metadata and generated summaries.
    text = ' '.join(str(record.get('abstract') or '').split())
    return hashlib.sha256(text.encode('utf-8')).hexdigest() if text else ''


def load_promotion_history(data_dir: Path, target: date, *, days: int = HISTORY_DAYS) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 1 <= days <= HISTORY_DAYS:
        raise ValueError('promotion history must be bounded to 1..14 days')
    rows = []
    evidence: dict[str, Any] = {'days': days, 'loaded': [], 'missing': [], 'unusable': []}
    for offset in range(1, days + 1):
        day = target - timedelta(days=offset)
        path = daily_data_path(day, data_dir)
        if not path.exists():
            evidence['missing'].append(day.isoformat())
            continue
        try:
            if path.stat().st_size > MAX_HISTORY_BYTES:
                raise ValueError('history file exceeds byte budget')
            payload = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(payload, dict):
                raise ValueError('legacy list lacks promotion provenance')
            meta = payload.get('metadata', {})
            if meta.get('quality_status') not in {'authoritative', 'authoritative_backfill'}:
                raise ValueError('not a controlled prior publication')
            records = payload.get('records', [])
            if not isinstance(records, list) or len(records) > MAX_HISTORY_RECORDS:
                raise ValueError('invalid or over-budget history records')
            evidence['loaded'].append({'date': day.isoformat(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            for r in records:
                if isinstance(r, dict):
                    rows.append({**r, '_promotion_date': day.isoformat()})
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            evidence['unusable'].append({'date': day.isoformat(), 'reason': str(exc)})
    return rows, evidence


def classify_event(record: dict[str, Any], prior: list[dict[str, Any]]) -> tuple[str, list[str]]:
    keys = identity_keys(record)
    if not keys:
        return 'IDENTITY_UNCERTAIN', []
    matches = [p for p in prior if keys & identity_keys(p)]
    for previous in matches:
        previous_keys = identity_keys(previous)
        for namespace in ('arxiv:', 'doi:', 'eprint:'):
            left = {k for k in keys if k.startswith(namespace)}
            right = {k for k in previous_keys if k.startswith(namespace)}
            if left and right and left.isdisjoint(right):
                return 'IDENTITY_UNCERTAIN', sorted({str(p.get('_promotion_date') or '') for p in matches})
    if not matches:
        version = authoritative_version(record)
        return ('GENUINE_NEW_VERSION' if version and int(version[1:]) > 1 else 'NEW_DISTINCT_PAPER'), []
    dates = sorted({str(p.get('_promotion_date') or '') for p in matches})
    current_version = authoritative_version(record)
    fingerprint = content_fingerprint(record)
    for previous in matches:
        old_version = authoritative_version(previous)
        old_fingerprint = content_fingerprint(previous)
        if current_version and old_version and current_version == old_version and fingerprint and fingerprint == old_fingerprint:
            metadata_fields = ('title', 'authors', 'venue', 'doi', 'update_date', 'source_metadata_correction_date')
            changed = any(record.get(f) != previous.get(f) for f in metadata_fields)
            return ('METADATA_ONLY_UPDATE' if changed else 'UNCHANGED_CROSS_DAY_DUPLICATE'), dates
    known_versions = [authoritative_version(p) for p in matches if authoritative_version(p)]
    if current_version and known_versions and int(current_version[1:]) > max(int(v[1:]) for v in known_versions):
        return 'GENUINE_NEW_VERSION', dates
    # A changed abstract is only a revision with source-authenticated revision-date evidence.
    revision_date = record.get('update_timestamp') or record.get('update_date')
    if fingerprint and all(content_fingerprint(p) and content_fingerprint(p) != fingerprint for p in matches):
        if record.get('update_date_kind') == 'AUTHORITATIVE_CONTENT_REVISION_DATE' and revision_date and all(str(revision_date) > str(p.get('update_timestamp') or p.get('update_date') or '') for p in matches):
            return 'GENUINE_CONTENT_REVISION', dates
    if not current_version and fingerprint and any(content_fingerprint(p) == fingerprint for p in matches):
        return 'METADATA_ONLY_UPDATE', dates
    return 'IDENTITY_UNCERTAIN', dates


def apply_promotion_history(records: list[PaperRecord], prior: list[dict[str, Any]]) -> list[PaperRecord]:
    result = []
    for record in records:
        event, dates = classify_event(record.model_dump(), prior)
        update: dict[str, Any] = {'cross_day_event': event, 'prior_promotion_dates': dates}
        if event != 'NEW_DISTINCT_PAPER':
            update.update(primary_today_new_eligible=False, primary_action_allowed=False)
            update['freshness_bucket'] = (record.freshness_bucket if event in {'GENUINE_NEW_VERSION', 'GENUINE_CONTENT_REVISION'} else ('date_uncertain_todo_verify' if event == 'IDENTITY_UNCERTAIN' else 'cross_day_duplicate'))
            update['freshness_reason'] = event + '; prior promotions=' + ','.join(dates)
        result.append(record.model_copy(update=update))
    return result
