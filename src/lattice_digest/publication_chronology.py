"""Precision-preserving chronology and non-counting late-discovery evidence."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import re
from lattice_digest.promotion_history import identity_keys


def precision(value):
    if not value:return 'UNKNOWN'
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(value)):return 'DATE_ONLY'
    return 'SOURCE_TIMESTAMP'


def late_discoveries(records, prior, start, end, identity, event_id, *, observed_through=None):
    known=set().union(*(identity_keys(p) for p in prior)) if prior else set()
    output=[];seen=set()
    from lattice_digest.scientific_scope import evaluate_scope
    observed_through=observed_through or datetime.now(timezone.utc)
    for index,row in enumerate(records):
        keys=identity_keys(row)
        if not keys or keys&known or row.get('publication_event_blockers'):continue
        if not evaluate_scope(row)['lattice_relevance_qualified']:continue
        if not str(row.get('source_url','')).startswith(('https://eprint.iacr.org/','https://arxiv.org/')):continue
        original=row.get('preprint_first_posted_at') or row.get('publication_timestamp') or row.get('publication_date')
        observed=row.get('source_observed_at') or row.get('first_seen_at')
        if not original or not observed:continue
        try:
            obs=datetime.fromisoformat(observed.replace('Z','+00:00'))
            # A real fetch normally happens AFTER the fixed publication cutoff.
            # Keep its actual observation time; do not slide publication coverage.
            if obs.tzinfo is None or not start<=obs<=observed_through:continue
            if precision(original)=='DATE_ONLY':
                # Conservative latest bound; date-only timezone is not invented.
                # Even UTC-12 end-of-day must be before coverage to call it late.
                latest=datetime.fromisoformat(original).replace(tzinfo=timezone.utc)+timedelta(hours=36)
                if latest>start or latest<start-timedelta(days=14):continue
            else:
                try:pub=datetime.fromisoformat(original.replace('Z','+00:00'))
                except ValueError:pub=parsedate_to_datetime(original)
                if pub.tzinfo is None or pub>=start or pub<start-timedelta(days=14):continue
        except (TypeError,ValueError):continue
        canonical=identity(row)
        if canonical in seen:continue
        seen.add(canonical)
        output.append({'row_index':index,'canonical_identity':canonical,
            'event_id':event_id(canonical,'LATE_DISCOVERY',str(original)),
            'title':row['title'],'source_url':row['source_url'],
            'first_publication_time':original,'publication_time_precision':precision(original),
            'public_collector_observed_at':observed,'status':'LATE_ARRIVAL',
            'observed_after_publication_cutoff':obs>=end,
            'counts_as_new_publication':False,
            'reason':'Previously unobserved source-grounded paper; original event time precedes this window. Retrospective visibility does not prove original collection.'})
    return output
