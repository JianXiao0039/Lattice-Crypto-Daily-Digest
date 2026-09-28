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
