from datetime import date, timedelta
import json
from lattice_digest.authority import configured_sources
from lattice_digest.storage import publish_daily_pair
from lattice_digest.weekly_synthesis import build_weekly_synthesis, aggregate_records
from lattice_digest.monthly_synthesis import build_monthly_synthesis, render_markdown, build_core_paper, build_reading_priority
from lattice_digest.artifact_paths import daily_data_path, daily_digest_path


def health():
    return [{'source':s['name'],'health_status':'green','runtime_state':'complete'} for s in configured_sources() if s.get('enabled')]


def test_seven_present_one_semantic_failure_not_seven_valid(tmp_path):
    start=date(2026,8,31)
    for i in range(7):publish_daily_pair([],tmp_path,start+timedelta(days=i),source_health=health())
    path=daily_digest_path('2026-09-05',tmp_path/'digests')
    path.write_text(path.read_text(encoding='utf-8')+'\ncorrupted generation',encoding='utf-8')
    result=build_weekly_synthesis(tmp_path/'data',start,date(2026,9,6))
    assert len(result['coverage']['loaded_days'])==7
    assert len(result['coverage']['fully_valid_days'])==6
    assert result['coverage']['semantic_failed_days']==['2026-09-05']
    assert result['coverage']['authority_state']!='AUTHORITATIVE_COMPLETE'


def test_missing_daily_and_old_schema_not_zero_valid(tmp_path):
    publish_daily_pair([],tmp_path,date(2026,8,31),source_health=health())
    result=build_weekly_synthesis(tmp_path/'data',date(2026,8,31),date(2026,9,6))
    assert len(result['coverage']['missing_days'])==6
    assert len(result['coverage']['fully_valid_days'])==1


def test_weekly_repeated_primary_has_one_publication_event():
    row={'title':'LWE','arxiv_id':'2609.01448','source':'arxiv','source_url':'https://arxiv.org/abs/2609.01448v1','primary_today_new_eligible':True,'freshness_bucket':'primary_today_new','relevance_label':'A'}
    result=aggregate_records([(date(2026,9,2),{'records':[row]}),(date(2026,9,3),{'records':[row]})])
    assert len(result)==1 and result[0]['seen_dates']==['2026-09-02','2026-09-03']
    assert len(result[0]['publication_events'])==1


def test_metadata_only_high_score_cannot_create_supported_claims():
    row={'title':'LWE implementation','source':'dblp','source_url':'https://dblp.org/rec/test','relevance_score':99,'reading_priority_score':99,'relevance_label':'A','keywords_matched':['LWE'],'reason':'matched keyword LWE'}
    core=build_core_paper(row)
    queue=build_reading_priority([row])
    assert core['evidence_status']=='METADATA_ONLY'
    assert core['rationale']['confidence']=='METADATA_ONLY'
    assert core['reading_action']==core['rationale']['reading_action']=='Track Later'
    assert queue['Track Later'][0]['reading_action']=='Track Later'
    assert 'TODO_VERIFY' in core['rationale']['method']


def test_monthly_full_index_and_no_weekly_double_count(tmp_path):
    path=daily_data_path('2026-08-01',tmp_path/'data');path.parent.mkdir(parents=True)
    rows=[{'title':f'Unique LWE paper {i:03d}','arxiv_id':f'2608.{i:05d}','source':'arxiv','source_url':f'https://arxiv.org/abs/2608.{i:05d}','relevance_label':'A','reading_priority_score':90} for i in range(30)]
    path.write_text(json.dumps({'records':rows,'metadata':{}}))
    weekly=tmp_path/'data/2026/weekly/2026-W32.json';weekly.parent.mkdir(parents=True)
    weekly.write_text(json.dumps({'from_date':'2026-08-01','to_date':'2026-08-07','records':rows}))
    result=build_monthly_synthesis(tmp_path/'data','2026-08')
    assert result['total_unique_records']==30
    assert len(result['paper_index'])==30
    assert '2026-08-22' in result['missing_days']
    assert result['input_quality']['authority_state']!='AUTHORITATIVE_COMPLETE'
    md=render_markdown(result)
    for row in rows:assert row['title'] in md
    for values in result['reading_priority'].values():
        for row in values:assert row['reason'].startswith(row['reading_action'])
