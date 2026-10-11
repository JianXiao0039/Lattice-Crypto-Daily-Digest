"""Period outputs must preserve the distinction between facts and derived views."""
from copy import deepcopy
from datetime import date
import pytest
from lattice_digest.publication_events import POLICY_VERSION,period_views,period_evidence_caveat
from lattice_digest.weekly_synthesis import build_weekly_synthesis,render_markdown as weekly_markdown
from lattice_digest.monthly_synthesis import build_monthly_synthesis,render_markdown as monthly_markdown

DAY=date(2026,10,1)
def payload(tier, status='PASS', event_id='source-event-1'):
    ledger={'collections':{'primary_publication_events':[{'event_id':event_id}]}}
    row={'records':[{'title':'fixture source record'}],'metadata':{},'_daily_input_quality':{'semantic_status':status}}
    if tier=='derived':
        row.update(_period_event_ledger=ledger,_period_reconciliation='SOURCE_WINDOW_REPLAY_OF_PRE_P0_CONTROLLED_DAILY')
    elif tier=='current':
        row.update(publication_event_ledger=ledger);row['metadata']['publication_policy_version']=POLICY_VERSION
    return row

def test_reconstructed_legacy_event_stays_explicitly_derived():
    original=payload('derived');before=deepcopy(original)
    result=period_views([(DAY,original)])
    evidence=result['evidence_provenance']
    assert result['counts']['primary_publication_events']==1
    assert evidence['verified_current_schema_event_count']==0
    assert evidence['derived_historical_event_candidate_count']==1
    assert evidence['input_evidence_tiers'][0]['evidence_tier']=='DERIVED_HISTORICAL_EVENT_CANDIDATE'
    assert original==before
    assert '不是新观察到的当前模式事实' in period_evidence_caveat(result)

def test_current_schema_requires_actual_semantic_pass_for_verified_tier():
    result=period_views([(DAY,payload('current',status=None))])
    assert result['evidence_provenance']['verified_current_schema_event_count']==0
    assert result['evidence_provenance']['unassessed_event_count']==1

@pytest.mark.parametrize('status',['FAIL','UNKNOWN'])
def test_failed_or_unknown_input_does_not_gain_verified_or_derived_events(status):
    result=period_views([(DAY,payload('derived',status))])
    assert result['counts']['primary_publication_events']==0
    assert result['evidence_provenance']['derived_historical_event_candidate_count']==0
    assert result['evidence_provenance']['input_evidence_tiers'][0]['evidence_tier']=='UNRESOLVED_DAILY_INPUT'

def test_same_event_in_mixed_inputs_is_counted_once_at_verified_tier():
    result=period_views([(DAY,payload('derived')),(date(2026,10,2),payload('current'))])
    assert result['counts']['primary_publication_events']==1
    assert result['evidence_provenance']['verified_current_schema_event_count']==1
    assert result['evidence_provenance']['derived_historical_event_candidate_count']==0

def test_unversioned_archive_population_cannot_become_event_evidence():
    result=period_views([(DAY,payload('legacy'))])
    assert sum(result['counts'].values())==0
    assert result['evidence_provenance']['input_evidence_tiers'][0]['original_record_population']==1
    assert result['evidence_provenance']['input_evidence_tiers'][0]['evidence_tier']=='UNRESOLVED_LEGACY_ARCHIVE'

@pytest.mark.parametrize('kind',['weekly','monthly'])
def test_real_period_renderers_surface_event_evidence_boundary(tmp_path,kind):
    views=period_views([(DAY,payload('derived')),(date(2026,10,2),payload('current',event_id='source-event-2'))])
    if kind=='weekly':
        result=build_weekly_synthesis(tmp_path/'data',date(2026,9,28),date(2026,10,4));result['publication_event_views']=views
        text=weekly_markdown(result)
    else:
        result=build_monthly_synthesis(tmp_path/'data','2026-10');result['publication_event_views']=views
        text=monthly_markdown(result)
    assert '当前模式已核验事件 1' in text
    assert '旧日报重建候选 1' in text
    assert '输入齐全不等于来源覆盖完整' in text
