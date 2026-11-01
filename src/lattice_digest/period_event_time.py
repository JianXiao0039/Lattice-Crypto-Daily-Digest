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
