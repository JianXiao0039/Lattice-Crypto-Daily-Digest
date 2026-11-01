"""Official bounded ePrint update listing, never a first-publication ledger.

HTML fallback is limited to the site's public /days/<n> metadata page. The
observed update date is date-only; received/approved times remain unknown.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone, timedelta

from lattice_digest.models import make_paper_record
from lattice_digest.source_completeness import record_source_coverage
from lattice_digest.source_queries import QueryRequest


def parse_iacr_days(text: str):
    if not re.search(r'Papers updated in last \d+ days', text):
        raise ValueError('not an official ePrint update-list shape')
    records = []
    for block in text.split('<div class="d-flex mb-1">')[1:]:
        id_match = re.search(r'href="/(\d{4}/\d+)"', block)
        title = re.search(r'<div class="papertitle">(.*?)</div>', block, re.S)
        authors = re.search(r'<div class="summaryauthors">(.*?)</div>', block, re.S)
        abstract = re.search(r'class="paper-abstract">(.*?)</div>', block, re.S)
        updated = re.search(r'Last updated:(?:&nbsp;|\s)*(\d{4}-\d{2}-\d{2})', block)
        def clean(value):
            return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', value)).split())
        if not id_match or not title:
            continue
        identifier = id_match[1]
        records.append(make_paper_record(
            title=clean(title[1]), authors=[clean(a) for a in re.split(r', | and ', authors[1])] if authors else [],
            abstract=clean(abstract[1]) if abstract else '', source='iacr_eprint',
            source_url=f'https://eprint.iacr.org/{identifier}', paper_id=f'iacr:{identifier}',
            eprint_id=identifier, venue='IACR ePrint', publication_date=None,
            update_date=updated[1] if updated else None,
            update_date_kind='SOURCE_UPDATE_DATE_UNSPECIFIED', categories=['iacr_eprint']))
    if not records:
        raise ValueError("update-list contains no parseable paper metadata")
    return records


def fetch_iacr_days(context, config, fetch):
    days = min(31, max(7, int(config.get('historical_catchup_days', 31))))
    url = f'https://eprint.iacr.org/days/{days}'
    request = QueryRequest('native_iacr_bounded_updates', url, source_family='iacr_eprint', native_syntax='html')
    attempt = context.begin_query_attempt('iacr_eprint', request)
    path = context.cache_dir / f'iacr_days_{days}_{datetime.now(timezone.utc).date().isoformat()}.html'
    guard = path.with_suffix('.attempt.json')
    now = datetime.now(timezone.utc)
    if not path.exists():
        attempts = 0
        if guard.exists():
            try:
                prior = json.loads(guard.read_text(encoding='utf-8'))
                attempts = int(prior['attempts'])
                retry = datetime.fromisoformat(prior['next_eligible_retry'])
                if retry.tzinfo is None or attempts >= 2 or now < retry:
                    context.finish_query_attempt(attempt, status='skipped_by_guard', raw_candidates=None)
                    return []
            except (ValueError,TypeError,KeyError):
                context.finish_query_attempt(attempt, status='skipped_by_guard', raw_candidates=None)
                return []
        guard.write_text(json.dumps({'attempts':attempts+1,'attempt_time':now.isoformat(),
            'requested_interval':f'rolling_last_{days}_days',
            'next_eligible_retry':(now+timedelta(hours=6)).isoformat()}),encoding='utf-8')
    text = path.read_text(encoding='utf-8') if path.exists() else fetch(context, url, source_name='iacr_eprint')
    if text is None:
        context.finish_query_attempt(attempt, status='failed', raw_candidates=None, error_category='historical_batch_unavailable')
        record_source_coverage(context, 'iacr_eprint', state='SOURCE_PARTIAL', reason='IACR_HISTORICAL_BATCH_UNAVAILABLE',
                               requested_interval=f'rolling_last_{days}_days', unverified_interval=context.since.isoformat())
        return []
    try:
        records = parse_iacr_days(text)
    except ValueError:
        context.finish_query_attempt(attempt, status='failed', raw_candidates=None, error_category='parse_error')
        return []
    if not path.exists():
        path.write_text(text, encoding='utf-8')
    observed_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    traced = []
    for record in records:
        occurrence = context.record_raw_occurrence('iacr_eprint', attempt, raw_title=record.title,
            source_identifier=record.eprint_id, source_url=record.source_url,
            publication_date=None, update_date=record.update_date, abstract_present=bool(record.abstract), parser_result='PARSED')
        record = record.model_copy(update={'source_query_family':request.family_id, 'source_query_text':url,
            'retrieval_timestamp':datetime.now(timezone.utc).isoformat(), 'source_observed_at':observed_at,
            'first_seen_at':observed_at, 'query_ids':[request.query_id], 'raw_occurrence_ids':[occurrence]})
        context.record_normalized_candidate(occurrence,record)
        traced.append(record)
    context.finish_query_attempt(attempt, status='success', raw_candidates=len(records))
    record_source_coverage(context, 'iacr_eprint', state='SOURCE_PARTIAL', reason='IACR_ROLLING_UPDATE_LIST_NOT_PUBLICATION_LEDGER',
        scope='SOURCE_NATIVE_BOUNDED_UPDATES', requested_interval=f'rolling_last_{days}_days',
        observed_items=len(records), official_reported_results=(re.search(r'\((\d+) results\)',text).group(1) if re.search(r'\((\d+) results\)',text) else None),
        pagination_followed=False, pagination_policy='RESPECT_NOFOLLOW_BOUNDED_FIRST_PAGE', snapshot_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
        original_snapshot_observed_at=observed_at, historical_window_complete=False,
        date_semantics='LAST_UPDATED_DATE_ONLY_NOT_RECEIVED_OR_APPROVED',
        coverage_confidence='PARTIAL_BOUNDED_OBSERVATION')
    return traced
