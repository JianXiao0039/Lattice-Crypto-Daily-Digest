"""TEST_ONLY calendar boundary cases, not real publication evidence."""
from datetime import datetime, timezone, date, timedelta
from zoneinfo import ZoneInfo
import pytest
from lattice_digest.period_event_time import prove_event_time, source_time_interval
from lattice_digest.publication_events import period_views
from lattice_digest.daily_inputs import PERIOD_INPUT_POLICY_V43

SG = ZoneInfo('Asia/Singapore')


def proof(value, start='2026-10-01', end='2026-11-01', granularity='MONTH', **kw):
    return prove_event_time(value, datetime.fromisoformat(start).replace(tzinfo=SG),
                            datetime.fromisoformat(end).replace(tzinfo=SG), granularity=granularity, **kw)


@pytest.mark.parametrize('value,accepted', [('2026-10-02',True),('2026-10-31',False),
    ('2026-10-01',False),('2026-09-30',False),('2026-11-01',False),
    ('2026-10-31T15:59:59+00:00',True),('2026-10-31T16:00:00+00:00',False),
    ('2026-10-15T12:00:00',False),('invalid',False)])
def test_month_conservative_unknown_zone(value, accepted):
    result = proof(value)
    assert result['MONTH_EVENT_TIME_PROVEN'] is accepted
    assert result['event_authorized'] is False


def test_month_can_be_proven_without_daily_proof():
    assert proof('2026-10-15')['MONTH_EVENT_TIME_PROVEN']
    assert not proof('2026-10-15', '2026-10-14T21:00:00', '2026-10-16T09:00:00', 'DAILY_WINDOW')['DAILY_WINDOW_EVENT_TIME_PROVEN']
    assert proof('2026-10-31',source_timezone='Asia/Singapore')['MONTH_EVENT_TIME_PROVEN']


def test_week_boundary_unknown_zone_not_rounded():
    assert proof('2026-10-28','2026-10-26','2026-11-02','WEEK')['WEEK_EVENT_TIME_PROVEN']
    assert not proof('2026-11-01','2026-10-26','2026-11-02','WEEK')['WEEK_EVENT_TIME_PROVEN']


def test_invalid_bounds_fail_closed():
    with pytest.raises(ValueError):
        prove_event_time('2026-10-15',datetime(2026,10,1),datetime(2026,11,1),granularity='MONTH')
    assert source_time_interval('2026-02-30') is None
    assert source_time_interval('2026-03-08T02:30:00','America/New_York') is None
    assert source_time_interval('2026-10-15','Unknown/Zone') is None


def test_v43_diagnostics_preserve_counts_and_owner_conflict():
    events = []
    for offset in range(7):
        day = date(2026,10,26)+timedelta(days=offset)
        collection = {'primary_publication_events': [{'event_id':'same', 'row_index':0,
            'canonical_identity':'eprint:2026/1','event_date':'2026-10-28'}]} if offset in (2,3) else {}
        events.append((day, {'metadata':{'publication_policy_version':'scientific-publication-v4-v3'},
           '_daily_input_quality':{'semantic_status':'PASS'},
           'records':[{'eprint_id':'2026/1'}], 'publication_event_ledger':{'collections':collection}}))
    frozen = period_views(events)
    result = period_views(events,assessment_policy=PERIOD_INPUT_POLICY_V43)
    assert result['counts'] == frozen['counts']
    assert result['ownership_conflicts'] == frozen['ownership_conflicts']
    assert result['period_time_proofs']['events'][0]['WEEK_EVENT_TIME_PROVEN']
    assert result['evidence_provenance']['verified_current_schema_event_count'] == 0
    assert 'period_time_proofs' not in frozen
