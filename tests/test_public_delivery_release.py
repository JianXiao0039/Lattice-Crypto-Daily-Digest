"""P1 release boundaries, durable pending delivery and historical evidence canaries."""
from pathlib import Path
from datetime import date
import json
import subprocess
from types import SimpleNamespace
import pytest
import yaml
from lattice_digest.report_gate import GateError, verify
from lattice_digest.public_report import export, inspect_tree, project, validate_public
from lattice_digest.public_delivery import deliver, pending
from tests.test_public_report_pipeline import canonical, rewrite


def bare(tmp_path):
    target=tmp_path/'public.git'
    subprocess.run(['git','init','--bare',str(target)],check=True,capture_output=True)
    return str(target)


def test_delivery_real_local_remote_readback_and_idempotency(canonical,tmp_path):
    remote=bare(tmp_path)
    first=deliver(canonical,'daily','2026-09-22',remote=remote,approved=True)
    assert first['states']==['CANONICAL_GENERATED','CANONICAL_QA_VERIFIED','PUBLIC_EXPORT_VERIFIED',
        'PRIVACY_QA_VERIFIED','GITHUB_PUSH_VERIFIED','REMOTE_READBACK_VERIFIED']
    second=deliver(canonical,'daily','2026-09-22',remote=remote,approved=True)
    assert second['status']=='NO_OP' and first['remote_commit']==second['remote_commit']
    assert pending(canonical,'daily')==[]


def test_delivery_unavailable_preserves_verified_staging_and_canonical(canonical,tmp_path,monkeypatch):
    from lattice_digest import public_delivery as delivery
    before=(canonical/'data/2026/daily/2026-09-22.json').read_bytes()
    def deny(*args,**kw):raise GateError('REMOTE_PERMISSION_OR_TRANSPORT_DENIED','fixture denied')
    monkeypatch.setattr(delivery,'publish',deny)
    result=deliver(canonical,'daily','2026-09-22',remote=bare(tmp_path),approved=True)
    assert result['status']=='PUBLISH_PENDING'
    assert 'GITHUB_PUSH_VERIFIED' not in result['states']
    assert pending(canonical,'daily')==['2026-09-22']
    assert (canonical/'data/2026/daily/2026-09-22.json').read_bytes()==before
    inspect_tree(canonical/'audits/public-delivery/daily/2026-09-22'/result['public_generation_id'])


def test_concurrent_delivery_writer_fails_without_mutation(canonical):
    folder=canonical/'audits/public-delivery/daily/2026-09-22';folder.mkdir(parents=True)
    (folder/'writer.lock').write_text('active writer')
    with pytest.raises(GateError,match='PUBLISH_CONFLICT'):
        deliver(canonical,'daily','2026-09-22',approved=True)
    assert (folder/'writer.lock').read_text()=='active writer'


def test_explicit_approval_is_required_even_for_verified_candidate(canonical):
    with pytest.raises(GateError,match='PUBLICATION_NOT_APPROVED'):
        deliver(canonical,'daily','2026-09-22')


def period_pair(root,kind):
    from lattice_digest.period_delivery import publish_period
    from lattice_digest.weekly_synthesis import build_weekly_synthesis,write_weekly_outputs
    from lattice_digest.monthly_synthesis import build_monthly_synthesis,write_monthly_outputs
    if kind=='weekly':
        payload=build_weekly_synthesis(root/'data',date(2026,9,21),date(2026,9,27));writer=write_weekly_outputs
    else:payload=build_monthly_synthesis(root/'data','2026-09');writer=write_monthly_outputs
    payload.setdefault('metadata',{}).update(runtime_code_state='PUBLISHED_CLEAN_RUNTIME',runtime_command_profile=kind.upper())
    paths=SimpleNamespace(data_root=root/'data',digest_root=root/'digests')
    publish_period(payload,paths,writer)
    return '2026-W39' if kind=='weekly' else '2026-09'


@pytest.mark.parametrize('kind',['weekly','monthly'])
def test_historical_reconstruction_stays_provisional_and_publicly_labeled(canonical,tmp_path,kind):
    def legacy(p):
        p.pop('publication_event_ledger',None);p.pop('publication_history_evidence',None)
        p['metadata'].pop('publication_policy_version',None)
        p['metadata'].pop('publication_state',None)
        from lattice_digest.authority import derive_authority
        p['metadata']['selection_counts']=derive_authority(p['records'],p['source_health'])['selection_counts']
    rewrite(canonical,legacy)
    period=period_pair(canonical,kind)
    pair=verify(canonical,kind,period)
    public=project(pair)
    assert public['quality']=='PROVISIONAL_PUBLIC'
    assert public['event_count']==0 and public['historical_candidate_count']==1 and public['entry_count']==1
    assert public['papers'][0]['event_evidence']=='DERIVED_HISTORICAL_EVENT_CANDIDATE'
    assert any(i['event_evidence']=='MISSING_CANONICAL_INPUT' for i in public['input_evidence'])
    output=tmp_path/'safe';export(canonical,kind,period,output)
    assert '历史重建候选'.encode() in b''.join(inspect_tree(output)[1].values())
    public['quality']='VALID_DEGRADED_AUTHORITATIVE'
    with pytest.raises(GateError,match='EVENT_OWNERSHIP_INVALID'):validate_public(public)


def test_workflow_write_privilege_is_only_in_sanitized_publication_job():
    path=Path(__file__).resolve().parents[1]/'.github/workflows/daily.yml'
    workflow=yaml.safe_load(path.read_text())
    assert workflow['permissions']=={'contents':'read','actions':'read'}
    assert workflow['concurrency']['cancel-in-progress'] is False
    job=workflow['jobs']['publish'];assert job['needs']=='digest'
    assert job['permissions']=={'contents':'write','actions':'read'}
    for name,job in workflow['jobs'].items():
        for step in job['steps']:
            command=step.get('run','')
            assert 'git add' not in command and 'git push' not in command
            assert 'papers.db' not in command and 'force-add' not in command
            assert not any(k.startswith(('GMAIL','GOOGLE','SMTP')) for k in step.get('env',{}))
    command='\n'.join(s.get('run','') for s in workflow['jobs']['publish']['steps'])
    assert 'lattice_digest.public_publisher' in command and '--use-gh-credentials' in command
    assert 'set -euo pipefail' in command


def test_only_known_primary_identifier_http_urls_are_upgraded():
    from lattice_digest.public_report import normalized_source_url
    assert normalized_source_url('http://arxiv.org/abs/2401.12345')=='https://arxiv.org/abs/2401.12345'
    for value in ['http://unknown.invalid/abs/2401.12345','http://arxiv.org/abs/2401.12345?tracking=private',
                  'http://private@arxiv.org/abs/2401.12345','http://arxiv.org:8080/abs/2401.12345']:
        with pytest.raises(GateError,match='PUBLIC_PRIVACY_GATE_FAILED'):normalized_source_url(value)


def test_public_daily_target_cannot_shift_while_rehashing(canonical):
    from lattice_digest.report_gate import encoded,sha
    p=project(verify(canonical,'daily','2026-09-22'))
    p['period_end']='2026-09-23T09:00:00+08:00'
    p['public_generation_id']=sha(encoded(dict(p,public_generation_id='')))
    with pytest.raises(GateError,match='PERIOD_IDENTITY_INVALID'):validate_public(p)


def test_delivery_transport_timeout_is_pending_and_redacted(canonical,monkeypatch):
    from lattice_digest import public_delivery as delivery
    def timeout(*a,**k):raise subprocess.TimeoutExpired('private-command-canary',60)
    monkeypatch.setattr(delivery,'publish',timeout)
    receipt=deliver(canonical,'daily','2026-09-22',approved=True)
    assert receipt['status']=='PUBLISH_PENDING' and receipt['error_code']=='REMOTE_PUBLICATION_FAILED'
    assert 'private-command-canary' not in json.dumps(receipt)


def test_deployed_deduplicator_public_adapter_merge_is_explicitly_supported(canonical):
    from lattice_digest.models import PaperRecord
    from lattice_digest.dedup import deduplicate
    from lattice_digest.public_report import reviewed_public_adapters
    path=canonical/'data/2026/daily/2026-09-22.json'
    row=json.loads(path.read_bytes())['records'][0]
    first=PaperRecord(**{k:v for k,v in row.items() if k in PaperRecord.model_fields})
    second=first.model_copy(deep=True);second.source='crossref'
    merged=deduplicate([first,second])
    assert len(merged)==1 and merged[0].source==first.source+', crossref'
    assert reviewed_public_adapters(merged[0].source)==(first.source,'crossref')
    rewrite(canonical,lambda p:p['records'][0].update(source=merged[0].source))
    assert project(verify(canonical,'daily','2026-09-22'))['event_count']==1


@pytest.mark.parametrize('value',['arxiv, unreviewed','arxiv,crossref','arxiv, arxiv','arxiv, ../notes','arxiv, gmail'])
def test_unknown_or_mail_adapter_merge_never_crosses_the_public_boundary(value):
    from lattice_digest.public_report import reviewed_public_adapters
    with pytest.raises(GateError,match='PUBLIC_PRIVACY_GATE_FAILED'):reviewed_public_adapters(value)


def test_cloud_clock_receipt_constructs_only_allowlisted_timing_fields():
    from lattice_digest.cloud_daily import execution_receipt,resolve_target
    target=resolve_target('2026-09-22T06:00:00Z','2026-09-22T06:01:00Z','schedule')
    secret='PRIVATE_HTTP_QUERY_OR_HEADER_CANARY'
    receipt=execution_receipt(target,{'source_query_runtime':[{
        'started_at':'2026-09-22T06:01:01Z','finished_at':'2026-09-22T06:01:02Z',
        'query':secret,'headers':secret}], 'runtime_paths':secret})
    assert receipt['actual_collection_start']=='2026-09-22T06:01:01+00:00'
    assert receipt['actual_collection_end']=='2026-09-22T06:01:02+00:00'
    assert receipt['source_attempt_count']==1 and receipt['report_target_date']=='2026-09-22'
    assert secret not in json.dumps(receipt) and 'query' not in receipt
