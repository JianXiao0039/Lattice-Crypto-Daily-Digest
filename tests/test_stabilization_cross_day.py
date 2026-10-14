from datetime import date, datetime, timezone
import json
from pathlib import Path
import pytest
from lattice_digest.models import make_paper_record
from lattice_digest.promotion_history import apply_promotion_history, classify_event, load_promotion_history
from lattice_digest.radar_freshness import enrich_record_for_daily_radar
from lattice_digest.artifact_paths import daily_data_path


def paper(**changes):
    fields = dict(title='LWE cryptanalysis', abstract='Source evidence for LWE.', source='arxiv',
                  source_url='https://arxiv.org/abs/2609.01448v1', arxiv_id='2609.01448',
                  publication_date='2026-09-01', update_date='2026-09-01', relevance_label='A', relevance_score=90)
    fields.update(changes)
    return make_paper_record(**fields)


@pytest.mark.parametrize(('changes','event'), [
    ({}, 'UNCHANGED_CROSS_DAY_DUPLICATE'),
    ({'source_url':'https://arxiv.org/abs/2609.01448v2'}, 'GENUINE_NEW_VERSION'),
    ({'abstract':'New source results.', 'update_date':'2026-09-03'}, 'GENUINE_CONTENT_REVISION'),
    ({'venue':'New venue'}, 'METADATA_ONLY_UPDATE'),
    ({'arxiv_id':'2609.09999', 'source_url':'https://arxiv.org/abs/2609.09999v1'}, 'NEW_DISTINCT_PAPER'),
    ({'abstract':''}, 'IDENTITY_UNCERTAIN'),
])
def test_event_matrix(changes, event):
    prior = [{**paper().model_dump(), '_promotion_date':'2026-09-02'}]
    current = paper(**changes)
    assert classify_event(current.model_dump(), prior)[0] == event
    updated = apply_promotion_history([current], prior)[0]
    refreshed = enrich_record_for_daily_radar(updated, date(2026,9,3))
    if event != 'NEW_DISTINCT_PAPER':
        assert not refreshed.primary_today_new_eligible


def test_missing_preceding_daily_searches_bounded_history(tmp_path):
    path = daily_data_path('2026-09-01', tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'metadata':{'quality_status':'authoritative'}, 'records':[{**paper().model_dump(), 'primary_today_new_eligible':True}]}))
    history, evidence = load_promotion_history(tmp_path,date(2026,9,3))
    assert '2026-09-02' in evidence['missing']
    assert classify_event(paper().model_dump(),history)[0] == 'UNCHANGED_CROSS_DAY_DUPLICATE'
    assert len(evidence['missing']) + len(evidence['loaded']) == 14
    with pytest.raises(ValueError):
        load_promotion_history(tmp_path,date(2026,9,3),days=1000)


def test_evidence_rich_archive_above_old_limit_preserves_overlapping_event_identity(tmp_path):
    from lattice_digest.publication_events import build_event_ledger
    prior = paper(publication_date='2026-09-02', update_date='2026-09-02').model_dump(mode='json')
    path = daily_data_path('2026-09-02', tmp_path)
    path.parent.mkdir(parents=True)
    data = json.dumps({'metadata': {'quality_status': 'authoritative'}, 'records': [prior]}).encode()
    path.write_bytes(data + b' ' * (17 * 1024 * 1024))
    history, evidence = load_promotion_history(tmp_path, date(2026,9,3))
    assert [item['date'] for item in evidence['loaded']] == ['2026-09-02']
    assert not evidence['unusable']
    assert classify_event(prior, history)[0] == 'UNCHANGED_CROSS_DAY_DUPLICATE'
    metadata = {'target_date': '2026-09-03', 'coverage_start': '2026-09-01T21:00:00Z',
                'coverage_end': '2026-09-03T09:00:00Z'}
    assert build_event_ledger([prior], metadata, history)['counts']['primary_new'] == 0


def test_history_still_rejects_archive_above_new_bounded_limit(tmp_path):
    from lattice_digest.promotion_history import MAX_HISTORY_BYTES
    path = daily_data_path('2026-09-02', tmp_path)
    path.parent.mkdir(parents=True)
    with path.open('wb') as stream:
        stream.write(b'{}')
        stream.truncate(MAX_HISTORY_BYTES + 1)
    history, evidence = load_promotion_history(tmp_path, date(2026,9,3))
    assert not history
    assert evidence['unusable'] == [{'date': '2026-09-02', 'reason': 'history file exceeds byte budget'}]


def test_real_september_canary():
    fixture = json.loads((Path(__file__).parent/'fixtures/stabilization_incidents.json').read_text(encoding='utf-8'))
    prior = fixture['2026-09-02']['records']
    current = fixture['2026-09-03']['records'][0]
    assert current['arxiv_id'] == '2609.01448'
    assert classify_event(current, prior)[0] == 'UNCHANGED_CROSS_DAY_DUPLICATE'
    result = apply_promotion_history([paper(**current)], prior)[0]
    assert not result.primary_today_new_eligible
    assert result.cross_day_event == 'UNCHANGED_CROSS_DAY_DUPLICATE'


def test_v2_is_revision_without_history():
    assert classify_event(paper(source_url='https://arxiv.org/abs/2609.01448v2').model_dump(),[])[0] == 'GENUINE_NEW_VERSION'


def test_old_control_remains_stale():
    record = enrich_record_for_daily_radar(paper(publication_date='2015-01-01', update_date='2015-01-01'), date(2026,9,3))
    assert not apply_promotion_history([record],[])[0].primary_today_new_eligible
