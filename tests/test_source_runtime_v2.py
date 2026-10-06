from datetime import date, datetime, timezone, timedelta
import io
import json
from pathlib import Path
import subprocess
from urllib.error import HTTPError

import pytest
from lattice_digest.authority import derive_authority
from lattice_digest.daily_continuity import audit_daily_continuity
from lattice_digest.evidence_contract import propagate_source_health
from lattice_digest.failure_scope import FailureScope, failure_scope
from lattice_digest.http import HttpResponse, HttpWarning, request_json, request_text
from lattice_digest.models import make_paper_record
from lattice_digest.runtime_provenance import runtime_provenance, public_runtime_allowed, schedule_telemetry
from lattice_digest.source_queries import QueryRequest, fair_query_schedule
from lattice_digest.sources.base import FetchContext, fetch_json


def context(tmp_path, **values):
    return FetchContext(root=tmp_path, since=datetime(2026, 10, 6, tzinfo=timezone.utc), dry_run=False, **values)


@pytest.mark.parametrize('category,scope', [
    ('invalid_request','QUERY_LOCAL'), ('not_acceptable','QUERY_LOCAL'), ('invalid_query','QUERY_LOCAL'),
    ('time_budget','FAMILY_LOCAL'), ('timeout','TRANSPORT_FAILURE'), ('ssl_error','TRANSPORT_FAILURE'),
    ('server_error','PROVIDER_WIDE'), ('rate_limit','RATE_LIMIT_DEFERRED'), ('malformed_response','MALFORMED_RESPONSE')])
def test_explicit_failure_scope(category, scope):
    assert failure_scope(category).value == scope


@pytest.mark.parametrize('category', ['not_acceptable','invalid_request','invalid_query'])
def test_query_local_failures_do_not_poison_provider(tmp_path, category):
    ctx = context(tmp_path)
    for _ in range(10):
        ctx.note_request_result('provider', ok=False, failure_category=category)
    assert ctx.request_allowed('provider') and not ctx.health('provider').circuit_open
    assert ctx.health('provider').consecutive_failures == 0
    assert ctx.health('provider').last_failure_scope == 'QUERY_LOCAL'


def test_family_local_is_not_provider_circuit(tmp_path):
    ctx = context(tmp_path)
    for _ in range(10):
        ctx.note_request_result('provider', ok=False, failure_category='invalid_query', scope=FailureScope.FAMILY_LOCAL)
    assert ctx.request_allowed('provider') and ctx.health('provider').last_failure_scope == 'FAMILY_LOCAL'


@pytest.mark.parametrize('category', ['timeout','server_error','malformed_response'])
def test_provider_circuit_stops_transport_outage_or_repeated_malformed(tmp_path, category):
    ctx = context(tmp_path)
    for _ in range(3):
        ctx.note_request_result('provider', ok=False, failure_category=category)
    assert not ctx.request_allowed('provider') and ctx.health('provider').circuit_open
    assert ctx.request_allowed('another-provider')


def test_short_retry_after_then_run_wide_defer_preserves_partial(tmp_path, monkeypatch):
    calls = []
    def limited(*args, **kwargs):
        calls.append(1)
        return None, HttpResponse(False, 'https://provider.test', warning=HttpWarning('https://provider.test', status_code=429, retry_after=2))
    monkeypatch.setattr('lattice_digest.sources.base.request_json', limited)
    ctx = context(tmp_path)
    ctx.register_source({'name':'provider','source_roles':['DISCOVERY_SECONDARY']})
    for _ in range(10):
        assert fetch_json(ctx, 'https://provider.test', source_name='provider') is None
    ctx.finish_source('provider', 5)
    health = ctx.health('provider')
    assert len(calls) == 1 and health.requests_skipped == 9
    assert health.partial_results_preserved and health.last_failure_scope == 'RATE_LIMIT_DEFERRED'


def test_429_retries_at_most_once_and_honors_retry_after(tmp_path):
    calls, sleeps = [], []
    def opener(request, timeout):
        calls.append(1)
        raise HTTPError(request.full_url, 429, 'limited', {'Retry-After':'2'}, io.BytesIO(b'limited'))
    response = request_text('https://limit.test', user_agent='test', cache_dir=tmp_path, open_func=opener,
                            min_interval_seconds=0, max_retries=10, sleep_func=sleeps.append)
    assert not response.ok and len(calls) == 2 and sleeps == [2]


class Response:
    status = 200
    headers = {'Content-Type':'text/html'}
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def geturl(self): return 'https://dblp.test/blocked'
    def read(self): return b'<html>anti-bot challenge</html>' + b'x' * 1000


def test_dblp_200_html_diagnostics_are_bounded_not_valid_metadata(tmp_path):
    data, response = request_json('https://dblp.test/api', user_agent='test', cache_dir=tmp_path,
                                  min_interval_seconds=0, open_func=lambda *a,**kw: Response())
    assert data is None and not response.ok and response.status_code == 200
    assert response.content_type == 'text/html' and response.effective_url == 'https://dblp.test/blocked'
    assert len(response.warning.response_body_preview) <= 500
    assert response.redirect_chain is None  # urllib does not expose the full chain.
    assert not list(tmp_path.glob('*.body'))


def test_valid_cache_reuse_makes_no_second_network_call(tmp_path):
    calls=[]
    class Valid(Response):
        headers={'Content-Type':'application/json'}
        def read(self): return b'{"result":{"hits":{"hit":[]}}}'
    def opener(*a, **kw): calls.append(1); return Valid()
    for _ in range(2):
        data, response = request_json('https://dblp.test/valid', user_agent='test', cache_dir=tmp_path,
                                      min_interval_seconds=0, open_func=opener)
        assert data['result']['hits']['hit'] == []
    assert len(calls) == 1 and response.from_cache


def test_round_robin_balances_repeated_families_and_preserves_query_semantics():
    requests = [QueryRequest(family, f'{family}-{i}') for family in ['critical','normal','other'] for i in range(4)]
    order = fair_query_schedule(requests)
    assert [r.family_id for r in order[:6]] == ['critical','normal','other'] * 2
    assert sorted((r.query_id,r.query_text) for r in order) == sorted((r.query_id,r.query_text) for r in requests)
    assert fair_query_schedule(requests, rotation=1)[0].family_id == 'normal'


def test_bounded_arxiv_partial_budget_rotates_starved_tail(tmp_path, monkeypatch):
    from lattice_digest.sources.arxiv import ArxivSource
    clock = [100.0]
    successful = []
    requests = {'name':'arxiv','url':'https://arxiv.test','query_groups':[['LWE'],['SIS'],['NTRU'],['BKZ']], 'source_roles':['DISCOVERY_PRIMARY']}
    def fake_fetch(ctx,url,source_name):
        if not ctx.request_allowed(source_name): return None
        clock[0] += 4
        successful.append(url)
        return '<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2610.12345v1</id><title>LWE</title><summary>LWE source</summary><published>2026-10-06T00:00:00Z</published></entry></feed>'
    monkeypatch.setattr('lattice_digest.sources.arxiv.fetch_text',fake_fetch)
    for offset in range(4):
        clock[0] = 100.0
        ctx = context(tmp_path / str(offset), monotonic_func=lambda:clock[0], per_source_time_budget_seconds=7)
        ctx.since += timedelta(days=offset)
        ctx.register_source(requests)
        records = ArxivSource(requests).fetch(ctx)
        ctx.finish_source('arxiv',len(records))
        assert len(records) == 1 and ctx.health('arxiv').query_groups_success == 2
        assert ctx.health('arxiv').query_groups_failed == 2 and ctx.health('arxiv').partial_results_preserved
        assert ctx.health('arxiv').runtime_reason_code == 'SOURCE_TIME_BUDGET_EXHAUSTED'
    assert len(set(successful)) == 4


def test_source_roles_determine_authority_without_provider_name_heuristics():
    configs = [{'name':'metadata-any-name','source_roles':['METADATA_ENRICHMENT','VENUE_AUTHORITY'], 'enabled':True},
               {'name':'discovery-any-name','source_roles':['DISCOVERY_PRIMARY'], 'enabled':True}]
    health = [{'source':'discovery-any-name','runtime_state':'complete','health_status':'green','query_groups_total':1,'query_groups_success':1},
              {'source':'metadata-any-name','runtime_state':'partial','health_status':'red','error_type':'malformed_response'}]
    decision=derive_authority([],health,source_configs=configs)
    assert decision['source_coverage']['complete']
    assert decision['source_coverage']['incomplete_required_sources'] == []
    assert decision['source_coverage']['degraded_sources'] == ['metadata-any-name']
    health[0]['runtime_state']='partial'
    assert derive_authority([],health,source_configs=configs)['source_coverage']['incomplete_required_sources'] == ['discovery-any-name']


def test_observed_health_propagates_with_source_roles(tmp_path):
    ctx=context(tmp_path)
    ctx.register_source({'name':'iacr_eprint','source_roles':['DISCOVERY_PRIMARY']})
    ctx.finish_source('iacr_eprint',1)
    record=make_paper_record(title='LWE',source='iacr_eprint',source_url='https://eprint.iacr.org/2026/1')
    mapped=propagate_source_health([record],ctx.source_health_summary())[0]
    assert mapped.source_health == 'green'
    assert mapped.source_health_provenance['iacr_eprint']['source_roles'] == ['DISCOVERY_PRIMARY']


def init_repo(root):
    root.mkdir()
    def git(*args): return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.DEVNULL)
    git('init','-b','main'); git('config','user.name','test'); git('config','user.email','test@example.test')
    (root/'src').mkdir(); (root/'src/runtime.py').write_text('version=1\n')
    (root/'docs').mkdir(); (root/'docs/note.md').write_text('baseline')
    git('add','--','src/runtime.py','docs/note.md'); git('commit','-m','baseline')
    git('update-ref','refs/remotes/origin/main','HEAD')
    return git


def test_runtime_states_are_only_about_production_dependencies(tmp_path):
    root=tmp_path/'repo';git=init_repo(root)
    initial=runtime_provenance(root)
    assert initial['runtime_code_state']=='PUBLISHED_CLEAN_RUNTIME'
    (root/'docs/note.md').write_text('dirty docs')
    (root/'scripts').mkdir()
    (root/'scripts/adhoc_research_audit.py').write_text('not a runtime entrypoint')
    assert runtime_provenance(root)['runtime_code_state']=='PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_FILES'
    assert runtime_provenance(root)['runtime_code_manifest_sha256']==initial['runtime_code_manifest_sha256']
    git('add','--','docs/note.md');git('commit','-m','docs only')
    # The untracked audit script remains unrelated dirty even after a docs commit.
    assert runtime_provenance(root)['runtime_code_state']=='PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_FILES'
    (root/'src/runtime.py').write_text('version=2\n')
    dirty=runtime_provenance(root)
    assert dirty['runtime_code_state']=='UNPUBLISHED_RUNTIME_CODE' and dirty['runtime_dirty_production_paths']==['src/runtime.py']
    assert dirty['runtime_code_manifest_sha256']!=initial['runtime_code_manifest_sha256']
    git('add','--','src/runtime.py');git('commit','-m','unpublished runtime')
    unpublished=runtime_provenance(root)
    assert unpublished['runtime_code_state']=='UNPUBLISHED_RUNTIME_CODE' and unpublished['runtime_dirty_production_paths']==[]
    assert unpublished['runtime_unpublished_production_paths']==['src/runtime.py']
    assert not public_runtime_allowed(unpublished,public_automation=True)


def test_unknown_provenance_fails_closed_only_public_automation(tmp_path):
    info=runtime_provenance(tmp_path)
    assert info['runtime_code_state']=='UNKNOWN_RUNTIME_PROVENANCE'
    assert not public_runtime_allowed(info,public_automation=True)
    assert public_runtime_allowed(info,public_automation=False)


def test_canonical_daily_blocks_unpublished_code_before_network(tmp_path,monkeypatch):
    from lattice_digest import run
    monkeypatch.setattr(run,'project_root',lambda:tmp_path)
    monkeypatch.setattr('lattice_digest.runtime_provenance.runtime_provenance',lambda root:{'runtime_code_state':'UNPUBLISHED_RUNTIME_CODE'})
    monkeypatch.setattr(run,'_collect_records',lambda *a:pytest.fail('network must not run'))
    assert run.main(['--since','36h'])==2


def test_continuity_gaps_are_read_only_and_do_not_invent_trigger_causes(tmp_path):
    data=tmp_path/'data';(data/'2026/daily').mkdir(parents=True)
    md=tmp_path/'digests/2026/daily';md.mkdir(parents=True)
    (data/'2026/daily/2026-09-26.json').write_text(json.dumps({'metadata':{'target_date':'2026-09-26'},'records':[]}))
    (md/'2026-09-26.md').write_text('Daily')
    (md/'2026-09-25-error.md').write_text('run failed')
    result=audit_daily_continuity(data,date(2026,9,25),date(2026,9,27))
    assert result['paired_days']==1 and result['gap_count']==2
    assert [g['gap_cause'] for g in result['gaps']]==['ERROR_ONLY_ARTIFACT','UNKNOWN']
    assert not (data/'2026/daily/2026-09-27.json').exists()


def test_continuity_target_mismatch_and_explicit_removed_evidence(tmp_path):
    data=tmp_path/'data';(data/'2026/daily').mkdir(parents=True)
    (data/'2026/daily/2026-09-25.json').write_text(json.dumps({'metadata':{'target_date':'2026-09-26'},'records':[]}))
    result=audit_daily_continuity(data,date(2026,9,25),date(2026,9,27),trigger_records=[{'target_date':'2026-09-27','gap_cause':'ARTIFACT_REMOVED','evidence':'test audit fact'}])
    assert result['gaps'][0]['gap_cause']=='TARGET_DATE_RESOLUTION_MISMATCH'
    assert result['gaps'][-1]['gap_cause']=='ARTIFACT_REMOVED'


@pytest.mark.parametrize('scheduled',['','nonsense','2026-10-06T09:00:00'])
def test_unknown_scheduler_metadata_remains_unknown(scheduled):
    value=schedule_telemetry(datetime(2026,10,6,1,5,tzinfo=timezone.utc),environ={'LATTICE_DIGEST_SCHEDULED_FOR':scheduled})
    assert value['scheduled_for']=='UNKNOWN' and value['schedule_lag_seconds']=='UNKNOWN'
    assert value['trigger_kind']=='UNKNOWN' and value['run_finished_at']=='UNKNOWN'


def test_known_schedule_serialization_and_real_lag():
    start=datetime(2026,10,6,1,5,tzinfo=timezone.utc)
    value=schedule_telemetry(start,start+timedelta(minutes=2),environ={
        'LATTICE_DIGEST_SCHEDULED_FOR':'2026-10-06T09:00:00+08:00',
        'LATTICE_DIGEST_TRIGGER_KIND':'SCHEDULED','LATTICE_DIGEST_SCHEDULE_TIMEZONE':'Asia/Singapore'})
    assert value['schedule_lag_seconds']==300 and value['trigger_kind']=='SCHEDULED'
    assert value['run_finished_at']==(start+timedelta(minutes=2)).isoformat()
    assert json.loads(json.dumps(value))==value
