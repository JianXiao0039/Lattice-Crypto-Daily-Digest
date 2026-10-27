"""Read-only, explicit-period validation of the existing canonical contracts.

Source coverage and execution authority are independent. Degradation is a
diagnostic, never a requirement to pretend that failed providers succeeded.
"""
from __future__ import annotations

import argparse
import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import re

from lattice_digest import artifact_paths as ap
from lattice_digest.public_contract import _reject_redirects


class GateError(ValueError):
    def __init__(self, code: str, detail: str):
        self.code = code
        # Details must be fixed diagnostics, never source prose or filesystem paths.
        super().__init__(f"{code}: {detail}")


def fail(code: str, detail: str):
    raise GateError(code, detail)


def encoded(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def strict_json(raw: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail('SCHEMA_INVALID', 'duplicate JSON key')
            result[key] = value
        return result
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                          parse_constant=lambda _: fail('SCHEMA_INVALID', 'non-finite JSON number'))
    except (UnicodeError, json.JSONDecodeError):
        fail('SCHEMA_INVALID', 'JSON must be valid UTF-8')


def period_bounds(kind: str, period: str) -> tuple[date, date]:
    try:
        if kind == 'daily' and re.fullmatch(r'\d{4}-\d{2}-\d{2}', period):
            first = last = date.fromisoformat(period)
        elif kind == 'weekly' and re.fullmatch(r'\d{4}-W\d{2}', period):
            first = date.fromisocalendar(int(period[:4]), int(period[-2:]), 1)
            last = first + timedelta(days=6)
        elif kind == 'monthly' and re.fullmatch(r'\d{4}-\d{2}', period):
            first = date.fromisoformat(period + '-01')
            last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
        else:
            raise ValueError
    except (ValueError, TypeError):
        fail('PERIOD_IDENTITY_INVALID', 'expected an explicit valid daily, ISO weekly, or monthly period')
    return first, last


def paths_for(root: Path, kind: str, period: str) -> tuple[Path, Path]:
    period_bounds(kind, period)
    return (getattr(ap, kind + '_data_path')(period, root=root / 'data'),
            getattr(ap, kind + '_digest_path')(period, root=root / 'digests'))


def safe_file(root: Path, path: Path, maximum: int = 64 * 1024 * 1024) -> bytes:
    try:
        _reject_redirects(root)
        _reject_redirects(path)
    except ValueError:
        fail('ARTIFACT_PATH_MISMATCH', 'redirected artifact path')
    if not path.absolute().is_relative_to(root.absolute()):
        fail('ARTIFACT_PATH_MISMATCH', 'artifact escapes selected root')
    if not path.is_file():
        fail('ARTIFACT_PATH_MISMATCH', 'canonical pair missing; legacy paths are not eligible')
    if not 0 < path.stat().st_size <= maximum:
        fail('PAYLOAD_SIZE_INVALID', 'artifact empty or oversized')
    return path.read_bytes()


@dataclass
class VerifiedPair:
    kind: str
    period: str
    payload: dict
    json_sha256: str
    markdown_sha256: str
    diagnostics: list[str]
    source_rows: list[dict]
    events: list[dict]
    start: str
    end: str
    coverage_state: str
    quality: str
    input_provenance: list[dict] = field(default_factory=list)


def verify(root: Path, kind: str, period: str) -> VerifiedPair:
    root = Path(root).absolute()
    if ap.legacy_fallback_allowed():
        fail('ARTIFACT_PATH_MISMATCH', 'public validation requires canonical-only input resolution; disable legacy compatibility')
    first, last = period_bounds(kind, period)
    j, m = paths_for(root, kind, period)
    lock_paths = [root / 'audits' / 'writer-locks' / f'{kind.upper()}-{period}.lock',
                  j.with_name('.' + period + '.publication.lock')]
    for lock in lock_paths:
        try:
            _reject_redirects(lock)
        except ValueError:
            fail('ARTIFACT_PATH_MISMATCH', 'redirected writer-state path')
    if any(p.exists() or p.is_symlink() for p in lock_paths):
        fail('PUBLISH_CONFLICT', 'active or stale writer lock; inspect before recovery')
    jb, mb = safe_file(root, j), safe_file(root, m)
    payload = strict_json(jb)
    try:
        md = mb.decode('utf-8')
    except UnicodeError:
        fail('SCHEMA_INVALID', 'Markdown must be UTF-8')
    if not isinstance(payload, dict) or not isinstance(payload.get('metadata'), dict):
        fail('SCHEMA_VERSION_UNSUPPORTED', 'unversioned list or missing metadata is not publish eligible')
    meta = payload['metadata']
    generation = meta.get('generation_id')
    if not isinstance(generation, str) or not re.fullmatch(r'[a-f0-9]{32}', generation):
        fail('PAIR_GENERATION_INVALID', 'missing or invalid generation ID')
    if md.count('<!-- generation:' + generation + ' -->') != 1:
        fail('PAIR_GENERATION_INVALID', 'Markdown generation marker mismatch')
    if sha(mb) != meta.get('markdown_sha256'):
        fail('PAIR_HASH_MISMATCH', 'Markdown byte hash mismatch')
    if not md.startswith('# ') or len(md.strip()) < 40:
        fail('READABLE_REPORT_INVALID', 'readable-report-v1 requires a heading and substantive report')
    if meta.get('publication_state') != 'QA_PASSED' or any(
            meta.get(k, {}).get('status') != 'PASS' for k in ('structural_qa', 'semantic_qa')):
        fail('DURABLE_QA_INVALID', 'independent QA cannot replace missing durable QA')
    from lattice_digest.publication_events import SUPPORTED_POLICIES, CORE_EVENTS
    diagnostics = []
    input_provenance = []
    derived_history = False
    if kind == 'daily':
        if meta.get('publication_policy_version') not in SUPPORTED_POLICIES or meta.get('authority_policy_version') != 'daily-correctness-v1':
            fail('SCHEMA_VERSION_UNSUPPORTED', 'unsupported Daily publication/authority policy tuple')
        if payload.get('schema_version') is not None:
            fail('SCHEMA_VERSION_UNSUPPORTED', 'unknown Daily schema')
        if meta.get('target_date') != period:
            fail('PERIOD_IDENTITY_INVALID', 'Daily target differs from explicit execution target')
        if meta.get('collector') not in ('github_actions', 'local_codex') or meta.get('run_mode') not in ('daily', 'backfill'):
            fail('RUNTIME_MODE_INVALID', 'unsupported collector or run mode')
        if meta.get('quality_status') not in ('authoritative', 'authoritative_backfill', 'provisional'):
            fail('RUNTIME_MODE_INVALID', 'unsupported execution quality')
        if meta['collector'] == 'github_actions' and meta['quality_status'] != 'provisional':
            fail('RUNTIME_MODE_INVALID', 'cloud collection cannot assert local authority')
        if meta['quality_status'] != 'provisional' and meta.get('runtime_code_state') not in (
                'PUBLISHED_CLEAN_RUNTIME', 'PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_WORKTREE'):
            fail('RUNTIME_MODE_INVALID', 'local authority requires published runtime provenance')
        try:
            start = datetime.fromisoformat(meta['coverage_start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(meta['coverage_end'].replace('Z', '+00:00'))
            from zoneinfo import ZoneInfo
            local_end = end.astimezone(ZoneInfo('Asia/Singapore')) if end.tzinfo else end
            midnight_end = (local_end.date() == last + timedelta(days=1) and
                            (local_end.hour,local_end.minute,local_end.second,local_end.microsecond) == (0,0,0,0))
            if not start.tzinfo or not end.tzinfo or start >= end or (local_end.date() != last and not midnight_end):
                raise ValueError
        except (KeyError, ValueError, AttributeError, TypeError):
            fail('PERIOD_IDENTITY_INVALID', 'invalid explicit Daily collection interval')
        rows = payload.get('records', [])
        events = [e for e in payload['publication_event_ledger']['decisions'] if e['collection'] in CORE_EVENTS]
        # Independently consult durable prior identities, not just the saved QA label.
        # This also catches a candidate that omitted its own historical observations.
        from lattice_digest.promotion_history import identity_keys, load_promotion_history, authoritative_version_conflicted
        for event in events:
            row=rows[event['row_index']]
            keys=identity_keys(row)
            if (not keys or authoritative_version_conflicted(row) or
                    any(len({k for k in keys if k.startswith(ns)})>1 for ns in ('doi:','arxiv:','eprint:'))):
                fail('SCIENTIFIC_QA_INCOMPLETE','counted event has unresolved conflicting source identities or versions')
        prior_rows, history = load_promotion_history(root/'data', first)
        prior_identities = set().union(*(identity_keys(row) for row in prior_rows)) if prior_rows else set()
        if any(e['collection']=='primary_publication_events' and identity_keys(rows[e['row_index']]) & prior_identities for e in events):
            fail('CROSS_DAY_DUPLICATE_PRIMARY', 'primary identity already observed in durable canonical history')
        if history.get('complete') is not True:
            codes = {e.get('code') for e in history.get('unusable', [])}
            code = ('HISTORY_INDEX_SOURCE_MISMATCH' if 'HISTORY_INDEX_SOURCE_MISMATCH' in codes else
                    'HISTORY_RESOURCE_LIMIT' if 'HISTORY_RESOURCE_LIMIT' in codes else 'HISTORY_EVIDENCE_UNUSABLE')
            fail(code, 'bounded independent history evidence is incomplete; publication is blocked')
        # Detect source changes after generation; saved metadata is not a trusted
        # index and cannot substitute for freshly read, source-bound evidence.
        saved_history = meta.get('promotion_history') or {}
        expected_hashes = {p.get('date'):p.get('sha256') for p in saved_history.get('loaded', [])}
        current_hashes = {p.get('date'):p.get('sha256') for p in history.get('loaded', [])}
        if any(current_hashes.get(day) != digest for day,digest in expected_hashes.items()):
            fail('HISTORY_INDEX_SOURCE_MISMATCH', 'historical source binding changed since generation')
        from lattice_digest.publication_events import build_event_ledger
        independently_rebuilt = build_event_ledger(rows, meta, prior_rows)
        if independently_rebuilt != payload['publication_event_ledger']:
            fail('EVENT_OWNERSHIP_CONFLICT', 'saved event ledger differs from independently source-bound historical replay')
        from lattice_digest.authority import semantic_qa
        qa = semantic_qa(payload, md)
        if qa['status'] != 'PASS' or meta.get('cross_day_qa', {}).get('status') != 'PASS':
            fail('SCIENTIFIC_QA_INCOMPLETE', 'independent Daily semantic/event QA rejected the pair')
        state = qa['derived_authority']['authority_state']
        start_text, end_text = start.isoformat(), end.isoformat()
        cloud = meta['quality_status'] == 'provisional'
    else:
        # Both deployed synthesizers use integer schema 1. A boolean is not a version.
        if type(payload.get('schema_version')) is not int or payload['schema_version'] != 1:
            fail('SCHEMA_VERSION_UNSUPPORTED', 'unsupported period synthesis schema')
        identity = payload.get('week_id') if kind == 'weekly' else payload.get('month')
        if identity != period or (kind == 'weekly' and (payload.get('from_date'), payload.get('to_date')) != (str(first), str(last))):
            fail('PERIOD_IDENTITY_INVALID', 'period metadata differs from explicit execution target')
        copy = strict_json(jb)
        saved = copy['metadata'].pop('payload_content_sha256', None)
        if saved != sha(encoded(copy)):
            fail('PAIR_HASH_MISMATCH', 'period structured payload hash mismatch')
        from lattice_digest.period_delivery import period_qa
        if period_qa(payload, md)['status'] != 'PASS':
            fail('EVENT_OWNERSHIP_INVALID', 'independent period QA rejected the pair')
        # Rebuild event views from the canonical Daily evidence. Never trust saved counts.
        from lattice_digest.weekly_synthesis import build_weekly_synthesis
        from lattice_digest.monthly_synthesis import build_monthly_synthesis
        rebuilt = (build_weekly_synthesis(root / 'data', first, last) if kind == 'weekly'
                   else build_monthly_synthesis(root / 'data', period))
        if rebuilt.get('publication_event_views') != payload.get('publication_event_views'):
            fail('EVENT_OWNERSHIP_INVALID', 'period event views differ from independent canonical replay')
        quality = payload.get('coverage') or payload.get('input_quality') or {}
        rebuilt_quality = rebuilt.get('coverage') or rebuilt.get('input_quality') or {}
        if quality.get('authority_state') != rebuilt_quality.get('authority_state'):
            fail('EVENT_OWNERSHIP_INVALID', 'period input authority differs from independent replay')
        if meta.get('runtime_code_state') not in ('PUBLISHED_CLEAN_RUNTIME', 'PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_WORKTREE'):
            fail('RUNTIME_MODE_INVALID', 'period requires published runtime provenance')
        allowed_profiles = {'MONTHLY','MONTHLY_EXPORTS','MONTHLY_OBSIDIAN'} if kind == 'monthly' else {'WEEKLY'}
        if meta.get('runtime_command_profile') not in allowed_profiles:
            fail('RUNTIME_MODE_INVALID', 'period runtime command profile mismatch')
        events, rows = [], []
        from lattice_digest.weekly_synthesis import load_daily_json
        from lattice_digest.publication_events import normalize_period_inputs
        days = [first + timedelta(days=i) for i in range((last-first).days+1)]
        loaded, missing = load_daily_json(root/'data', days)
        for cursor, source_payload in normalize_period_inputs(loaded):
            source_j, source_m = paths_for(root, 'daily', str(cursor))
            source_jb, source_mb = safe_file(root, source_j), safe_file(root, source_m)
            source_meta = source_payload.get('metadata', {})
            generation = source_meta.get('generation_id')
            if (not isinstance(generation, str) or not re.fullmatch(r'[a-f0-9]{32}', generation)
                    or source_mb.decode('utf-8').count('<!-- generation:' + generation + ' -->') != 1
                    or sha(source_mb) != source_meta.get('markdown_sha256')):
                fail('PAIR_HASH_MISMATCH', 'period Daily input pair has no verified byte binding')
            if source_meta.get('target_date') != str(cursor):
                fail('PERIOD_IDENTITY_INVALID', 'period Daily input target mismatch')
            assessment = source_payload.get('_daily_input_quality', {})
            ledger = source_payload.get('_period_event_ledger', source_payload.get('publication_event_ledger', {}))
            selected = [e for e in ledger.get('decisions', []) if e.get('collection') in CORE_EVENTS]
            if source_meta.get('publication_policy_version'):
                daily = verify(root, 'daily', str(cursor))
                source_rows, selected = daily.source_rows, daily.events
                tier = 'VERIFIED_CURRENT_SCHEMA_EVENT'
            elif selected:
                # A bounded historical source-window reconstruction remains a candidate.
                # This does not invent current-schema durable QA or runtime provenance.
                if (assessment.get('semantic_status') != 'PASS'
                        or source_meta.get('structural_qa', {}).get('status') != 'PASS'
                        or source_meta.get('semantic_qa', {}).get('status') != 'PASS'
                        or source_meta.get('authority_policy_version') != 'daily-correctness-v1'
                        or source_meta.get('collector') != 'local_codex'
                        or source_meta.get('quality_status') not in ('authoritative', 'authoritative_backfill')):
                    fail('DURABLE_QA_INVALID', 'historical event candidate lacks controlled source QA')
                source_rows = source_payload['records']
                from lattice_digest.promotion_history import identity_keys, HISTORY_DAYS
                previous = set()
                for offset in range(1, HISTORY_DAYS+1):
                    previous_path = ap.daily_data_path(cursor-timedelta(days=offset), root/'data')
                    if previous_path.is_file():
                        previous_payload = strict_json(safe_file(root, previous_path))
                        if isinstance(previous_payload,dict):
                            for row in previous_payload.get('records',[]):
                                if isinstance(row,dict): previous.update(identity_keys(row))
                if any(e['collection']=='primary_publication_events' and
                       identity_keys(source_rows[e['row_index']]) & previous for e in selected):
                    fail('EVENT_OWNERSHIP_INVALID', 'historical primary already observed in prior Daily inputs')
                tier = 'DERIVED_HISTORICAL_EVENT_CANDIDATE'
                derived_history = True
                diagnostics.append('HISTORICAL_EVENT_RECONSTRUCTION')
            else:
                # Noncontributing historical gaps cannot become a no-news fact.
                source_rows, selected = [], []
                tier = 'NONCONTRIBUTING_HISTORICAL_INPUT'
                diagnostics.append('HISTORICAL_INPUT_NOT_CURRENT_SCHEMA_VERIFIED')
            input_provenance.append({'date':str(cursor), 'json_sha256':sha(source_jb),
                'markdown_sha256':sha(source_mb), 'event_evidence':tier})
            offset = len(rows)
            rows.extend(source_rows)
            events.extend({**e, 'row_index':e['row_index']+offset, 'event_evidence':tier} for e in selected)
        for missing_date in missing:
            input_provenance.append({'date':missing_date, 'event_evidence':'MISSING_CANONICAL_INPUT'})
        # Revisions and primary events remain distinct; repeated overlap is one event.
        unique = {e['event_id']: e for e in events}
        expected = {e['event_id'] for k, v in payload['publication_event_views']['collections'].items() if k in CORE_EVENTS for e in v}
        if set(unique) != expected:
            fail('EVENT_OWNERSHIP_INVALID', 'period contains unverified, missing or inflated events')
        events = list(unique.values())
        state = quality['authority_state']
        start_text, end_text = str(first), str(last)
        cloud = False
    if state != 'AUTHORITATIVE_COMPLETE':
        diagnostics.append('SOURCE_COVERAGE_DEGRADED')
    quality = ('PROVISIONAL_PUBLIC' if cloud or derived_history else 'VERIFIED_AUTHORITATIVE' if state == 'AUTHORITATIVE_COMPLETE'
               else 'VALID_DEGRADED_AUTHORITATIVE')
    return VerifiedPair(kind, period, payload, sha(jb), sha(mb), diagnostics, rows, events,
                        start_text, end_text, state, quality, input_provenance)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--type', required=True, choices=('daily', 'weekly', 'monthly'))
    parser.add_argument('--period', required=True)
    args = parser.parse_args(argv)
    try:
        pair = verify(args.root, args.type, args.period)
        print(json.dumps({'gate': 'PRODUCTION_REPORT_GATE', 'status': 'PASS', 'report_type': pair.kind,
                          'report_period': pair.period, 'diagnostics': pair.diagnostics,
                          'json_sha256': pair.json_sha256, 'markdown_sha256': pair.markdown_sha256}))
        return 0
    except (GateError, OSError, ValueError, TypeError, KeyError):
        import sys
        exc = sys.exception()
        print(json.dumps({'gate': 'PRODUCTION_REPORT_GATE', 'status': 'FAIL',
                          'code': exc.code if isinstance(exc, GateError) else 'SCHEMA_INVALID'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
