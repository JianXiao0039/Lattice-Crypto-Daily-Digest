"""V43 public noncounting contract; source-backed fixture and isolated Git tests."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from lattice_digest.public_report import validate_public, render, temporal_evidence, NO_AUTHORIZED_EVENTS_NOTICE
from lattice_digest.report_gate import GateError, sha, encoded
from tests.test_v41_delivery_states import delivery_fixture
from tests.test_public_report_pipeline import canonical

FIXTURE = Path(__file__).parent/'fixtures/v41_cloud_public/public26/daily/2026/2026-10-26.json'


def candidate():
    p=json.loads(FIXTURE.read_bytes())
    p.update(public_schema_version='public-literature-v3', readable_contract_version='public-readable-v3',
        quality='PROVISIONAL_PUBLIC', source_coverage=[dict(source='arxiv',health='yellow',runtime_state='partial')], papers=[], entry_count=0, event_count=0, historical_candidate_count=0,
        omitted_event_count=0, temporal_evidence=temporal_evidence({}),
        revision_reason='SOURCE_GROUNDED_READABILITY_AND_CLOCK_DISCLOSURE_V2', noncounting_observations=[],
        history_evidence=dict(contract='HISTORY_DEGRADED_NO_PROMOTION',outcome='NO_AUTHORIZED_EVENTS_OBSERVED',
            capability='CLOUD_PINNED_PUBLIC_OWNERSHIP',history_complete=False,unresolved_dates=['2026-10-17'],
            pending_noncounting_candidates=3))
    return seal(p)


def seal(p):
    p['public_generation_id']=''
    p['public_generation_id']=sha(encoded(p))
    return p


def test_partial_noncounting_report_discloses_history_and_unknown_clocks():
    p=validate_public(candidate())
    output=render(p).decode()
    assert NO_AUTHORIZED_EVENTS_NOTICE in output
    assert '2026-10-17' in output and 'CLOUD_PINNED_PUBLIC_OWNERSHIP' in output
    assert p['temporal_evidence']['nominal_scheduled_time']=='UNKNOWN'
    assert 'VERIFIED_AUTHORITATIVE' not in output


@pytest.mark.parametrize('mutation',['events','highest_quality','complete','injection','bad_date','duplicate_dates'])
def test_noncounting_contract_cannot_upgrade_authority_or_inject_private_fields(mutation):
    p=candidate()
    if mutation=='events':
        original=json.loads(FIXTURE.read_bytes())
        p.update(papers=original['papers'],event_count=original['event_count'],entry_count=original['entry_count'])
    if mutation=='highest_quality':p['quality']='VERIFIED_AUTHORITATIVE'
    if mutation=='complete':p['history_evidence']['history_complete']=True
    if mutation=='injection':p['history_evidence']['gmail']='private-canary'
    if mutation=='bad_date':p['history_evidence']['unresolved_dates']=['C:/private/canary']
    if mutation=='duplicate_dates':p['history_evidence']['unresolved_dates']*=2
    with pytest.raises(GateError):validate_public(seal(p))


def test_superseded_report_is_readback_but_not_delivery_of_this_candidate(tmp_path,monkeypatch):
    from lattice_digest import public_delivery
    delivery_fixture(monkeypatch)
    monkeypatch.setattr(public_delivery,'publish',lambda *a,**k:dict(status='SUPERSEDED_BY_HIGHER_AUTHORITY',
        remote_readback='PASS',commit='f'*40,published_quality='VERIFIED_AUTHORITATIVE'))
    r=public_delivery.deliver(tmp_path,'daily','2026-10-27',approved=True)
    assert r['status']=='SUPERSEDED_BY_HIGHER_AUTHORITY'
    assert not r['publication_verified'] and not r['delivery_verified']
    assert r['remote_readback_verified']
    assert 'REMOTE_PUBLISHED' not in r.get('delivery_state_machine',[])
    assert 'GITHUB_PUSH_VERIFIED' not in r['states']


def test_zero_events_source_only_degradation_preserves_verified_history():
    p=candidate()
    p['history_evidence'].update(contract='SOURCE_DEGRADED_NO_PROMOTION', capability='LOCAL_CANONICAL_HISTORY', history_complete=True, unresolved_dates=[])
    validated=validate_public(seal(p))
    assert validated['history_evidence']['history_complete']
    assert 'SOURCE_DEGRADED_NO_PROMOTION' in render(validated).decode()
    assert validated['quality']=='PROVISIONAL_PUBLIC'


@pytest.mark.parametrize('capability', ['UNAVAILABLE_HISTORY', 'CLOUD_PINNED_PUBLIC_OWNERSHIP'])
def test_partial_history_capability_cannot_assert_source_only_degradation(capability):
    p = candidate()
    p['history_evidence'].update(contract='SOURCE_DEGRADED_NO_PROMOTION',
        capability=capability, history_complete=True, unresolved_dates=[])
    with pytest.raises(GateError, match='EVENT_OWNERSHIP_INVALID'):
        validate_public(seal(p))


def test_cloud_without_local_sources_or_public_pin_discloses_unavailable_history(tmp_path):
    from datetime import date
    from lattice_digest.storage import publish_daily_pair
    from lattice_digest.report_gate import verify
    from lattice_digest.public_report import project
    target = date(2026, 10, 18)
    metadata = dict(target_date=str(target), collector='github_actions',
        quality_status='provisional', run_mode='daily', trigger_kind='TEST_ONLY',
        coverage_start='2026-10-17T04:00:00+00:00', coverage_end='2026-10-18T16:00:00+00:00',
        test_evidence='TEST_ONLY_TRANSPORT_NO_SOURCE_HISTORY_OR_RUNTIME_AUTHORITY')
    health = [dict(source=name, health_status='red', runtime_state='failed')
              for name in ('arxiv', 'iacr_eprint', 'openalex', 'semantic_scholar')]
    publish_daily_pair([], tmp_path, target, metadata=metadata, source_health=health)
    public = project(verify(tmp_path, 'daily', str(target)))
    assert public['history_evidence']['capability'] == 'UNAVAILABLE_HISTORY'
    assert public['history_evidence']['history_complete'] is False
    assert len(public['history_evidence']['unresolved_dates']) == 14
    assert public['event_count'] == 0


def test_cloud_gate_demands_independent_snapshot_not_saved_rows(canonical):
    from tests.test_public_report_pipeline import rewrite
    from lattice_digest.cloud_public_history import ownership_history
    from lattice_digest.report_gate import verify
    root=Path(__file__).parent/'fixtures/v41_cloud_public/public26'
    _, evidence=ownership_history(root, '3dfa6cc5ec3c6850138459b4740b65b79fad4f5d', '2026-10-27')
    def cloud(p):
        p['metadata'].update(collector='github_actions',quality_status='provisional',public_ownership_evidence=evidence)
    rewrite(canonical,cloud)
    with pytest.raises(GateError,match='independent pinned public snapshot'):
        verify(canonical,'daily','2026-09-22')


def test_period_noncounting_partial_day_is_visible_and_contributes_no_event():
    p=json.loads(FIXTURE.read_bytes())
    p.update(report_type='weekly',report_period='2026-W44',title='格密码公开文献报告 2026-W44',
        period_start='2026-10-26',period_end='2026-11-01',quality='PROVISIONAL_PUBLIC',
        papers=[],entry_count=0,event_count=0,historical_candidate_count=0,omitted_event_count=0,
        input_evidence=[dict(date='2026-10-26',json_sha256='a'*64,markdown_sha256='b'*64,
            event_evidence='NONCOUNTING_PARTIAL_INPUT')])
    validated=validate_public(seal(p))
    assert validated['event_count']==0
    output=render(validated).decode()
    assert '来源输入限制日期：2026-10-26' in output
    assert '不能解释为没有新论文' in output
