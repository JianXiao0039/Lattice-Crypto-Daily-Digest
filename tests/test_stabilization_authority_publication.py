from datetime import date
import json
from pathlib import Path
import pytest
from lattice_digest.authority import derive_authority, semantic_qa, configured_sources, INCOMPLETE_ZERO_TEXT
from lattice_digest.digest import generate_markdown
from lattice_digest.models import make_paper_record
from lattice_digest.storage import publish_daily_pair
from scripts.verify_durable_artifacts import verify_daily, main


DAY = date(2026,9,17)


def health():
    return [{'source':s['name'], 'health_status':'green','runtime_state':'complete','query_groups_total':1,'query_groups_success':1} for s in configured_sources() if s.get('enabled')]


def record(**kwargs):
    return make_paper_record(title='LWE analysis',abstract='We study LWE security.',source='arxiv',source_url='https://arxiv.org/abs/2609.09991v1', arxiv_id='2609.09991', publication_date='2026-09-17',relevance_label='A',**kwargs)


@pytest.mark.parametrize(('rows','count','expected'), [(health(),0,'AUTHORITATIVE_COMPLETE'),([],0,'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'),([],1,'AUTHORITATIVE_DEGRADED')])
def test_authority_matrix(rows,count,expected):
    assert derive_authority([record()] if count else [],rows)['authority_state'] == expected


def test_roles_and_partial_are_not_source_name_hardcodes():
    config=[{'name':'new_required','source_roles':['DISCOVERY_PRIMARY']},{'name':'optional','source_roles':['ENRICHMENT']}]
    decision=derive_authority([],[],source_configs=config)
    assert decision['source_coverage']['incomplete_required_sources'] == ['new_required']
    assert derive_authority([record(security_impact_severity='CRITICAL',evidence_confidence='TODO_VERIFY')],health())['authority_state']=='PARTIAL_VERIFY_FIRST'


@pytest.mark.parametrize('field,value',[('query_groups_failed',1),('runtime_state','partial'),('circuit_open',True),('health_status','red'),('query_groups_success',0)])
def test_green_labels_do_not_hide_missing_coverage(field,value):
    rows=health()
    row=next(r for r in rows if r['source']=='arxiv')
    row[field]=value
    assert not derive_authority([],rows)['source_coverage']['complete']


def test_all_empty_sections_are_conservative_and_healthy_zero_survives():
    md=generate_markdown([],DAY,source_health=[],metadata={'source_starved':False,'quality_status':'authoritative','completion_state':'degraded_complete'})
    assert INCOMPLETE_ZERO_TEXT in md and '可跳过' not in md
    qa=semantic_qa({'records':[],'source_health':[]},md,candidate=True)
    assert qa['status']=='PASS'
    assert '最近 36 小时未发现满足当前格密码研究门槛的新论文。' in generate_markdown([],DAY,source_health=health())


@pytest.mark.parametrize('bad',['今日没有值得读的论文。','可跳过日报','nothing relevant today','no papers worth reading','safe to skip','今天没有相关论文','今日没有通过筛选的论文，因此没有研究进展'])
def test_semantic_contradiction_anywhere(bad):
    md=generate_markdown([],DAY,source_health=[])
    assert semantic_qa({'records':[],'source_health':[]},md+'\n'+bad,candidate=True)['status']=='FAIL'


def test_forged_authority_and_missing_semantics():
    md=generate_markdown([],DAY,source_health=[])
    p={'records':[],'source_health':[],'metadata':{'authority_state':'AUTHORITATIVE_COMPLETE'}}
    assert semantic_qa(p,md)['status']=='FAIL'
    p['metadata']={}
    assert semantic_qa(p,md)['status']=='UNKNOWN'


def test_missing_cli_compatibility_and_malformed_semantic_schema(tmp_path):
    assert main(['--root',str(tmp_path),'--date',DAY.isoformat()])==0
    md=generate_markdown([],DAY,source_health=[])
    assert semantic_qa({'records':[],'metadata':{'semantic_qa':True}},md)['status']=='UNKNOWN'


def test_concurrent_publisher_lock_refuses_collision(tmp_path):
    path=tmp_path/'data/2026/daily';path.mkdir(parents=True)
    lock=path/'.2026-09-17.publication.lock';lock.write_text('other owner')
    with pytest.raises(FileExistsError):publish_daily_pair([],tmp_path,DAY,source_health=[])
    assert lock.read_text()=='other owner'
    assert not (path/'2026-09-17.json').exists()


def test_pair_verifier_and_nonzero_semantic_exit(tmp_path):
    jp,mp=publish_daily_pair([],tmp_path,DAY,source_health=[{'source':'arxiv','health_status':'red','runtime_state':'partial'}])
    assert verify_daily(tmp_path,DAY.isoformat())['status']=='verified'
    mp.write_text(mp.read_text(encoding='utf-8')+'\nsafe to skip',encoding='utf-8')
    result=verify_daily(tmp_path,DAY.isoformat())
    assert result['structural_valid'] and not result['semantic_valid']
    assert main(['--root',str(tmp_path),'--date',DAY.isoformat()])==2
    assert not (tmp_path/'data/2026-09-17.json').exists()


def test_invalid_candidate_and_collision_preserve_previous_pair(tmp_path,monkeypatch):
    jp,mp=publish_daily_pair([],tmp_path,DAY,source_health=[])
    before=(jp.read_bytes(),mp.read_bytes())
    with pytest.raises(FileExistsError):publish_daily_pair([],tmp_path,DAY,source_health=[])
    original=__import__('lattice_digest.storage',fromlist=['generate_markdown']).generate_markdown
    monkeypatch.setattr('lattice_digest.storage.generate_markdown',lambda *a,**kw:original(*a,**kw)+'\nsafe to skip')
    with pytest.raises(ValueError):publish_daily_pair([],tmp_path,DAY,source_health=[],force=True)
    assert before==(jp.read_bytes(),mp.read_bytes())


def test_second_replace_failure_rolls_back_pair(tmp_path,monkeypatch):
    import lattice_digest.storage as storage
    jp,mp=publish_daily_pair([],tmp_path,DAY,source_health=[])
    before=(jp.read_bytes(),mp.read_bytes())
    replace=storage.os.replace
    def fail(src,dst):
        if Path(dst)==mp:raise OSError('injected second replacement failure')
        replace(src,dst)
    monkeypatch.setattr(storage.os,'replace',fail)
    with pytest.raises(OSError):publish_daily_pair([],tmp_path,DAY,source_health=[],force=True)
    assert before==(jp.read_bytes(),mp.read_bytes())


@pytest.mark.parametrize('day',['2026-09-05','2026-09-07','2026-09-17'])
def test_real_incomplete_incident(day):
    fixture=json.loads((Path(__file__).parent/'fixtures/stabilization_incidents.json').read_text(encoding='utf-8'))[day]
    md=generate_markdown([],date.fromisoformat(day),source_health=fixture['source_health'])
    assert semantic_qa(fixture,md,candidate=True)['status']=='PASS'
    assert derive_authority([],fixture['source_health'])['authority_state']=='INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'
