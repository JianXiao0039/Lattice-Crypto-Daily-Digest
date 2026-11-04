"""Conservative source-time interval proofs; never an event acceptance receipt.

A date without a source timezone spans every legal UTC offset (-12 to +14).
Submission, announcement and revision timestamps must be supplied separately by
the caller. This module neither substitutes discovery time nor changes owners.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo
import re

UTC = timezone.utc
POLICY = 'source-time-interval-v44'
EVENT_TIME_POLICY = 'source-time-evidence-v45'


def event_time_evidence(value, start, end, *, granularity='DAILY_WINDOW',
                        source_timezone=None, source_timezone_evidence=None,
                        evidence_kind=None):
    """Source-bound interval evidence, not a scientific event authorization.

    Only a separately verified source timezone rule may narrow a civil date.
    A collector observation is never a publication/revision time. Callers must
    independently bind the value and any timezone rule to the original source;
    passing this function a dictionary does not verify that rule's provenance.
    The independent gate recomputes this result from the bound source row.
    """
    # Producer coverage normalizes UTC, while the verifier reads the original
    # offset-bearing metadata. Canonicalize equivalent period instants before
    # serializing proof fields; this must not invent offsets for naive bounds.
    if isinstance(start, datetime) and start.tzinfo is not None:
        start = start.astimezone(UTC)
    if isinstance(end, datetime) and end.tzinfo is not None:
        end = end.astimezone(UTC)
    zone_evidence = source_timezone_evidence
    verified_zone = (isinstance(zone_evidence, dict)
        and zone_evidence.get('status') == 'VERIFIED'
        and isinstance(zone_evidence.get('timezone'), str)
        and bool(zone_evidence['timezone'])
        and isinstance(zone_evidence.get('source_url'), str)
        and zone_evidence['source_url'].startswith('https://')
        and isinstance(zone_evidence.get('rule'), str)
        and bool(zone_evidence['rule'].strip())
        and (source_timezone is None or source_timezone == zone_evidence['timezone']))
    zone = zone_evidence['timezone'] if verified_zone else None
    proof = prove_event_time(value, start, end, granularity=granularity, source_timezone=zone)
    precision = {'EXPLICIT_OFFSET_INSTANT': 'EXPLICIT_OFFSET_TIMESTAMP',
                 'DATE_ONLY_SOURCE_ZONE': 'SOURCE_TIMEZONE_VERIFIED_DATE',
                 'DATE_ONLY_UNKNOWN_ZONE': 'DATE_ONLY_UNKNOWN_TIMEZONE',
                 'NAIVE_TIME_SOURCE_ZONE': 'SOURCE_TIMEZONE_VERIFIED_TIMESTAMP'}.get(proof['precision'], 'UNVERIFIED_EVENT_TIME')
    if isinstance(value, str) and proof['precision'] == 'UNPROVEN':
        try:
            naive = datetime.fromisoformat(value)
            if naive.tzinfo is None:
                precision = 'NAIVE_TIMESTAMP_UNKNOWN_TIMEZONE'
        except ValueError:
            pass
    if evidence_kind in {'SOURCE_ASSERTED_NOTE_DATE', 'DATE_ONLY_SOURCE_NOTE'}:
        precision = 'SOURCE_ASSERTED_NOTE_DATE'
    if evidence_kind == 'COLLECTOR_OBSERVED_TIMESTAMP':
        precision = evidence_kind
    contained = proof[granularity + '_EVENT_TIME_PROVEN']
    obligations = []
    if evidence_kind == 'COLLECTOR_OBSERVED_TIMESTAMP':
        obligations.append('SOURCE_EVENT_TIME_NOT_COLLECTOR_OBSERVATION')
    if not contained:
        obligations.append('REQUESTED_PERIOD_CONTAINMENT_UNPROVEN')
    temporal = contained and not obligations
    return {**proof, 'policy_version': EVENT_TIME_POLICY,
            'source_date': value, 'source_date_precision': precision,
            'source_timezone_evidence': zone_evidence if verified_zone else None,
            'possible_earliest_utc': proof['possible_start'],
            'possible_latest_utc_exclusive': proof['possible_end_exclusive'],
            'target_period': {'granularity': granularity, 'start': start.isoformat(),
                              'end_exclusive': end.isoformat()},
            'containment_proven': temporal,
            granularity + '_EVENT_TIME_PROVEN': temporal,
            'unresolved_obligations': obligations,
            'event_authorized': False}


def daily_event_time_proof(value, start, end, *, source_timezone_evidence=None,
                           source_date_precision=None):
    """Daily convenience entry to the same source-time evidence contract."""
    return event_time_evidence(value, start, end,
        source_timezone_evidence=source_timezone_evidence,
        evidence_kind=source_date_precision)


def source_time_interval(value: str, source_timezone: str | None = None):
    """Return (earliest UTC, exclusive latest UTC, precision) or None.

Exact instants use a one-microsecond representational interval. Unknown offset
date-only bounds are intentionally wider than a UTC civil day. A supplied
timezone must itself come from independently verified source metadata.
"""
    if not isinstance(value, str):
        return None
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            day = date.fromisoformat(value)
            start = datetime.combine(day, time.min)
            end = start + timedelta(days=1)
            if source_timezone:
                zone = ZoneInfo(source_timezone)
                return start.replace(tzinfo=zone).astimezone(UTC), end.replace(tzinfo=zone).astimezone(UTC), 'DATE_ONLY_SOURCE_ZONE'
            return (start.replace(tzinfo=UTC)-timedelta(hours=14),
                    end.replace(tzinfo=UTC)+timedelta(hours=12), 'DATE_ONLY_UNKNOWN_ZONE')
        try:
            instant = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            instant = parsedate_to_datetime(value)
        if instant.tzinfo is None:
            if not source_timezone:
                return None
            # Civil clocks may be ambiguous at DST transitions: conservatively
            # include both folds instead of inventing a unique instant.
            zone = ZoneInfo(source_timezone)
            alternatives = [instant.replace(tzinfo=zone, fold=f).astimezone(UTC) for f in (0, 1)]
            alternatives = [t for t in alternatives if t.astimezone(zone).replace(tzinfo=None) == instant]
            if not alternatives:
                return None
            return min(alternatives), max(alternatives)+timedelta(microseconds=1), 'NAIVE_TIME_SOURCE_ZONE'
        instant = instant.astimezone(UTC)
        return instant, instant+timedelta(microseconds=1), 'EXPLICIT_OFFSET_INSTANT'
    except (ValueError, TypeError, OverflowError, KeyError, IndexError):
        return None


def prove_event_time(value, start, end, *, granularity, source_timezone=None):
    """Prove interval containment only; identity/scope/ownership remain pending."""
    if granularity not in {'MONTH', 'WEEK', 'DAILY_WINDOW'}:
        raise ValueError('UNSUPPORTED_TIME_PROOF_GRANULARITY')
    if not isinstance(start, datetime) or not isinstance(end, datetime) or start.tzinfo is None or end.tzinfo is None or start >= end:
        raise ValueError('INVALID_AWARE_PERIOD_INTERVAL')
    interval = source_time_interval(value, source_timezone)
    proven = bool(interval and start <= interval[0] and interval[1] <= end)
    return {'policy_version': POLICY, 'source_value': value,
            'source_timezone': source_timezone or 'UNKNOWN', 'granularity': granularity,
            'period_start': start.isoformat(), 'period_end_exclusive': end.isoformat(),
            'possible_start': interval[0].isoformat() if interval else None,
            'possible_end_exclusive': interval[1].isoformat() if interval else None,
            'precision': interval[2] if interval else 'UNPROVEN',
            granularity+'_EVENT_TIME_PROVEN': proven,
            'event_authorized': False,
            'remaining_obligations': ['SOURCE_BINDING', 'IDENTITY', 'EVENT_TYPE', 'OWNERSHIP', 'SCIENTIFIC_QA']}


def period_time_diagnostics(loaded, collections):
    """Add diagnostics only for explicitly complete calendar input spans.

No ledger event or count is changed. Input presence does not prove source
coverage, and a time proof does not make an old Daily candidate accepted.
"""
    days = sorted({day for day, _ in loaded})
    if not days or len(days) != (days[-1]-days[0]).days+1:
        return {'policy_version': POLICY, 'status': 'PERIOD_BOUNDS_UNPROVEN', 'events': []}
    first, last = days[0], days[-1]
    month_end = (last+timedelta(days=1)).day == 1
    granularity = ('MONTH' if first.day == 1 and first.year == last.year and first.month == last.month and month_end else
                   'WEEK' if first.weekday() == 0 and len(days) == 7 else None)
    if granularity is None:
        return {'policy_version': POLICY, 'status': 'PERIOD_BOUNDS_UNPROVEN', 'events': []}
    zone = ZoneInfo('Asia/Singapore')
    start = datetime.combine(first, time.min, zone)
    end = datetime.combine(last+timedelta(days=1), time.min, zone)
    events = []
    for name in ('primary_publication_events', 'revision_events', 'new_critical_verify_events'):
        for event in collections.get(name, {}).values():
            proof = prove_event_time(event.get('event_date'), start, end, granularity=granularity)
            events.append({'event_id': event.get('event_id'), 'canonical_identity': event.get('canonical_identity'),
                           'event_type': name, **proof})
    return {'policy_version': POLICY, 'status': 'TIME_DIAGNOSTICS_ONLY_NO_EVENT_PROMOTION', 'events': events}
