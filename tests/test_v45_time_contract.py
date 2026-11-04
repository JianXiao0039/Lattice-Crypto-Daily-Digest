"""TEST_ONLY interval and producer/verifier cases; no real event timestamps."""
from copy import deepcopy
from datetime import datetime

import pytest

from lattice_digest.period_event_time import event_time_evidence, daily_event_time_proof


def instant(value):
    return datetime.fromisoformat(value)


START = instant('2026-11-02T13:07:43.688654+00:00')
END = instant('2026-11-04T01:07:43.688654+00:00')
ZONE = {'status': 'VERIFIED', 'timezone': 'Asia/Singapore',
        'source_url': 'https://example.test/TEST_ONLY_timezone_rule',
        'rule': 'TEST_ONLY source civil dates use Singapore time'}


def test_nov03_unknown_timezone_entire_interval_crosses_daily_cutoff():
    proof = daily_event_time_proof('2026-11-03', START, END,
                                  source_date_precision='SOURCE_ASSERTED_NOTE_DATE')
    assert proof['source_date_precision'] == 'SOURCE_ASSERTED_NOTE_DATE'
    assert proof['possible_earliest_utc'] == '2026-11-02T10:00:00+00:00'
    assert proof['possible_latest_utc_exclusive'] == '2026-11-04T12:00:00+00:00'
    assert not proof['containment_proven']
    assert proof['unresolved_obligations'] == ['REQUESTED_PERIOD_CONTAINMENT_UNPROVEN']
    assert not proof['event_authorized']


def test_source_zone_requires_explicit_verified_rule_and_whole_day():
    proof = daily_event_time_proof('2026-11-03', START, END, source_timezone_evidence=ZONE)
    assert proof['containment_proven']
    assert proof['source_date_precision'] == 'SOURCE_TIMEZONE_VERIFIED_DATE'
    assert proof['possible_earliest_utc'] == '2026-11-02T16:00:00+00:00'
    assert proof['possible_latest_utc_exclusive'] == '2026-11-03T16:00:00+00:00'
    assert not daily_event_time_proof('2026-11-03', instant('2026-11-03T00:00:00+00:00'), END,
                                    source_timezone_evidence=ZONE)['containment_proven']


@pytest.mark.parametrize('evidence', [None, {'timezone': 'UTC'}, {**ZONE, 'status': 'UNVERIFIED'},
                                      {**ZONE, 'rule': ''}, {**ZONE, 'source_url': ''}])
def test_unverified_timezone_never_narrows_the_possible_interval(evidence):
    proof = event_time_evidence('2026-11-03', START, END,
                               source_timezone='UTC', source_timezone_evidence=evidence)
    assert not proof['containment_proven']
    assert proof['source_timezone_evidence'] is None


@pytest.mark.parametrize('value,accepted,precision', [
    ('2026-11-03T12:00:00+00:00', True, 'EXPLICIT_OFFSET_TIMESTAMP'),
    ('2026-11-04T01:07:43.688654+00:00', False, 'EXPLICIT_OFFSET_TIMESTAMP'),
    ('2026-11-03T12:00:00', False, 'NAIVE_TIMESTAMP_UNKNOWN_TIMEZONE'),
    ('2026-11-03', False, 'DATE_ONLY_UNKNOWN_TIMEZONE'),
    ('bad', False, 'UNVERIFIED_EVENT_TIME'),
])
def test_precision_taxonomy(value, accepted, precision):
    proof = daily_event_time_proof(value, START, END)
    assert proof['containment_proven'] is accepted
    assert proof['source_date_precision'] == precision


def test_collector_time_is_never_event_time_even_inside_window():
    proof = daily_event_time_proof('2026-11-03T12:00:00+00:00', START, END,
                                  source_date_precision='COLLECTOR_OBSERVED_TIMESTAMP')
    assert not proof['containment_proven']
    assert 'SOURCE_EVENT_TIME_NOT_COLLECTOR_OBSERVATION' in proof['unresolved_obligations']


@pytest.mark.parametrize('granularity,start,end', [
    ('WEEK', '2026-11-02T00:00:00+08:00', '2026-11-09T00:00:00+08:00'),
    ('MONTH', '2026-11-01T00:00:00+08:00', '2026-12-01T00:00:00+08:00'),
])
def test_period_membership_does_not_invent_daily_time(granularity, start, end):
    proof = event_time_evidence('2026-11-03', instant(start), instant(end), granularity=granularity)
    assert proof['containment_proven']
    assert proof['source_date_precision'] == 'DATE_ONLY_UNKNOWN_TIMEZONE'
    assert not daily_event_time_proof('2026-11-03', START, END)['containment_proven']


def test_producer_and_independent_gate_share_contract_and_preserve_pair(tmp_path):
    from lattice_digest.evidence_contract import bind_source_evidence
    from lattice_digest.models import make_paper_record
    from lattice_digest.storage import publish_daily_pair
    from lattice_digest.report_gate import verify
    from tests.test_public_report_pipeline import CANARIES, META, DAY
    from tests.test_nested_public_e2e import health
    from tests.v41_history_fixture import seed_empty_history

    root = tmp_path/'canonical'
    seed_empty_history(root, DAY)
    source = deepcopy(CANARIES[0]['source_record'])
    source.update(publication_timestamp='2026-09-22T00:30:00+00:00',
                  preprint_first_posted_at=None, announcement_date=None,
                  update_date=None, update_timestamp=None, source_version_timestamp=None)
    record = bind_source_evidence(make_paper_record(**source))
    jp, mp = publish_daily_pair([record], root, DAY, source_health=health(degraded=True),
        metadata={**META, 'publication_policy_version': 'scientific-publication-v45-v1'})
    original = jp.read_bytes(), mp.read_bytes()
    pair = verify(root, 'daily', str(DAY))
    assert len(pair.events) == 1
    entry = pair.events[0]
    assert entry['source_time_evidence'] == daily_event_time_proof(entry['event_date'],
        instant(META['coverage_start']), instant(META['coverage_end']),
        source_date_precision=entry['source_date_precision'])
    assert (jp.read_bytes(), mp.read_bytes()) == original
