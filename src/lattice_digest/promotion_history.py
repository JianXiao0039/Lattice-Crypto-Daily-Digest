"""Bounded, canonical-only publication history. Titles never establish identity."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit

from lattice_digest.artifact_paths import daily_data_path
from lattice_digest.history_resources import (load_verified_history_pair, HistoryEvidenceError,
    MAX_HISTORY_BYTES, MAX_HISTORY_RECORDS, MAX_TOTAL_COMPACT_BYTES)
from lattice_digest.models import PaperRecord

HISTORY_DAYS = 14
EVENTS = {
    'UNCHANGED_CROSS_DAY_DUPLICATE', 'GENUINE_NEW_VERSION',
    'GENUINE_CONTENT_REVISION', 'METADATA_ONLY_UPDATE',
    'NEW_DISTINCT_PAPER', 'IDENTITY_UNCERTAIN',
}


def identity_keys(record: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for field, prefix in [('doi', 'doi'), ('arxiv_id', 'arxiv'), ('eprint_id', 'eprint')]:
        value = unquote(str(record.get(field) or '').strip()).lower()
        value = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', value)
        value = re.sub(r'^(?:doi|arxiv|eprint):\s*', '', value)
        if prefix == 'arxiv':
            value = re.sub(r'^https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/', '', value)
            value = re.sub(r'\.pdf(?:[?#].*)?$', '', value)
        if prefix == 'eprint':
            value = re.sub(r'^https?://eprint\.iacr\.org/', '', value)
        if value:
            keys.add(prefix + ':' + (re.sub(r'v\d+$', '', value) if prefix == 'arxiv' else value))
    for value in [record.get('source_url'), record.get('paper_id'), *(record.get('source_urls') or [])]:
        text = unquote(str(value or '').strip()).lower()
        doi = re.search(r'(?:^doi:|https?://(?:dx\.)?doi\.org/)(10\.\d{4,9}/[^?#\s]+)', text)
        arxiv = re.search(r'(?:arxiv:|arxiv\.org/(?:abs|pdf)/)(\d{4}\.\d{4,5}|[a-z.-]+/\d{7})(?:v\d+)?', text)
        eprint = re.search(r'(?:eprint:|eprint\.iacr\.org/)(\d{4}/\d+)', text)
        if doi:
            keys.add('doi:' + doi[1].rstrip('/'))
        elif arxiv:
            keys.add('arxiv:' + arxiv[1])
        elif eprint:
            keys.add('eprint:' + eprint[1])
        elif text.startswith(('http://', 'https://')):
            parsed = urlsplit(text)
            # A fragment does not identify a different publication. Preserve
            # query parameters; they can be identity-bearing on publisher sites.
            keys.add('url:' + urlunsplit(('https', parsed.netloc, parsed.path.rstrip('/'), parsed.query, '')))
    return keys


def _authoritative_versions(record: dict[str, Any]) -> set[str]:
    versions = set()
    for value in [record.get('arxiv_id'), record.get('source_url'), record.get('paper_id')]:
        match = re.search(r'(?:\d{4}\.\d{4,5}|/\d{7})(v\d+)(?:\.pdf)?(?:[?#/]|$)', str(value or ''), re.I)
        if match:
            versions.add(match[1].lower())
    return versions


def authoritative_version_conflicted(record: dict[str, Any]) -> bool:
    return len(_authoritative_versions(record)) > 1


def authoritative_version(record: dict[str, Any]) -> str:
    versions = _authoritative_versions(record)
    return next(iter(versions)) if len(versions) == 1 else ''


def content_fingerprint(record: dict[str, Any]) -> str:
    # Compare source content, excluding mutable metadata and generated summaries.
    text = ' '.join(str(record.get('abstract') or '').split())
    return hashlib.sha256(text.encode('utf-8')).hexdigest() if text else ''


def load_promotion_history(data_dir: Path, target: date, *, days: int = HISTORY_DAYS) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 1 <= days <= HISTORY_DAYS:
        raise ValueError('promotion history must be bounded to 1..14 days')
    rows = []
    evidence: dict[str, Any] = {'schema_version': 'history-evidence-v41', 'days': days, 'loaded': [], 'missing': [], 'unusable': [],
        'state': 'COMPLETE', 'complete': True, 'primary_ownership_eligible': True,
        'compact_accounted_bytes': 0, 'reader_version': 'bounded-history-v41-1'}
    for offset in range(1, days + 1):
        day = target - timedelta(days=offset)
        path = daily_data_path(day, data_dir)
        if not path.exists() and not path.is_symlink():
            evidence['missing'].append(day.isoformat())
            continue
        try:
            records, receipt = load_verified_history_pair(data_dir, day)
            if evidence['compact_accounted_bytes'] + receipt['compact_accounted_bytes'] > MAX_TOTAL_COMPACT_BYTES:
                raise HistoryEvidenceError('HISTORY_RESOURCE_LIMIT')
            evidence['compact_accounted_bytes'] += receipt['compact_accounted_bytes']
            evidence['loaded'].append(receipt)
            rows.extend(records)
        except HistoryEvidenceError as exc:
            receipt = exc.receipt
            size = receipt.get('compact_accounted_bytes', 0)
            # Unverified but safely decoded observations can conservatively block
            # a repeat. They can never establish eligibility or a revision proof.
            if size and evidence['compact_accounted_bytes'] + size <= MAX_TOTAL_COMPACT_BYTES:
                evidence['compact_accounted_bytes'] += size
                rows.extend({**r, '_history_unverified': True, '_history_verified': False} for r in exc.rows)
            evidence['unusable'].append({'date': day.isoformat(), 'code': exc.code, 'reason': exc.code})
    if evidence['missing'] or evidence['unusable']:
        evidence.update(state='HISTORY_EVIDENCE_BLOCKED', complete=False, primary_ownership_eligible=False,
                        diagnostic='HISTORY_EVIDENCE_UNUSABLE')
    return rows, evidence


def classify_event(record: dict[str, Any], prior: list[dict[str, Any]]) -> tuple[str, list[str]]:
    keys = identity_keys(record)
    if (not keys or authoritative_version_conflicted(record)
            or any(len({k for k in keys if k.startswith(namespace)}) > 1 for namespace in ('arxiv:', 'doi:', 'eprint:'))):
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
        if ((current_version == old_version or not current_version and not old_version)
                and fingerprint and fingerprint == old_fingerprint):
            metadata_fields = ('title', 'authors', 'venue', 'doi', 'update_date', 'source_metadata_correction_date')
            changed = any(record.get(f) != previous.get(f) for f in metadata_fields)
            return ('METADATA_ONLY_UPDATE' if changed else 'UNCHANGED_CROSS_DAY_DUPLICATE'), dates
    if any(p.get('_history_verified') is False or authoritative_version_conflicted(p) for p in matches):
        return 'IDENTITY_UNCERTAIN', dates
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


def history_identity_index(prior: list[dict[str, Any]]) -> dict[str, set[int]]:
    index: dict[str, set[int]] = {}
    for position, row in enumerate(prior):
        for key in identity_keys(row):
            index.setdefault(key, set()).add(position)
    return index


def indexed_history_matches(row: dict[str, Any], prior: list[dict[str, Any]], index: dict[str, set[int]]) -> list[dict[str, Any]]:
    positions: set[int] = set()
    for key in identity_keys(row):
        positions.update(index.get(key, ()))
    return [prior[position] for position in sorted(positions)]


def apply_promotion_history(records: list[PaperRecord], prior: list[dict[str, Any]]) -> list[PaperRecord]:
    result = []
    index = history_identity_index(prior)
    for record in records:
        row = record.model_dump()
        event, dates = classify_event(row, indexed_history_matches(row, prior, index))
        update: dict[str, Any] = {'cross_day_event': event, 'prior_promotion_dates': dates}
        if event != 'NEW_DISTINCT_PAPER':
            update.update(primary_today_new_eligible=False, primary_action_allowed=False)
            update['freshness_bucket'] = (record.freshness_bucket if event in {'GENUINE_NEW_VERSION', 'GENUINE_CONTENT_REVISION'} else ('date_uncertain_todo_verify' if event == 'IDENTITY_UNCERTAIN' else 'cross_day_duplicate'))
            update['freshness_reason'] = event + '; prior promotions=' + ','.join(dates)
        result.append(record.model_copy(update=update))
    return result
