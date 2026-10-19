"""Late observations are a source-bound reading view, never period event counts."""
from copy import deepcopy
from datetime import date
import pytest
from lattice_digest.publication_events import period_views,period_late_markdown,POLICY_VERSION,LEGACY_POLICY_VERSION

def daily(**changes):
    row={'title':'Lattice commitment aggregation','abstract':'We construct lattice commitments from Module-SIS.',
         'source_url':'https://eprint.iacr.org/2026/2500','eprint_id':'2026/2500',
         'publication_timestamp':'Thu, 15 Oct 2026 06:55:07 +0000','source_observed_at':'2026-10-18T01:04:00+00:00',
         'relevance_score':90,'relevance_label':'A'}
    late={'row_index':0,'canonical_identity':'eprint:2026/2500','title':row['title'],'source_url':row['source_url'],
          'first_publication_time':row['publication_timestamp'],'publication_time_precision':'SOURCE_TIMESTAMP',
          'public_collector_observed_at':row['source_observed_at'],'event_id':'late-event',
          'status':'LATE_ARRIVAL','counts_as_new_publication':False}
    p={'metadata':{'publication_policy_version':POLICY_VERSION},'_daily_input_quality':{'semantic_status':'PASS'},
       'records':[row],'source_health':[{'source':'arxiv','health_status':'red','error_type':'timeout'}],
       'late_arrivals':[late],'publication_event_ledger':{'collections':{}}}
    p.update(changes);return p

def views(*payloads):return period_views([(date(2026,10,18+i),p) for i,p in enumerate(payloads)])

def test_verified_noncounting_view_preserves_times_health_scores_and_count_contract():
    p=daily();before=deepcopy(p);v=views(p);assert p==before
    item=v['late_discoveries'][0]
    assert item['first_publication_time']==p['late_arrivals'][0]['first_publication_time']
    assert item['public_collector_observed_at']==p['records'][0]['source_observed_at']
    assert item['publication_time_precision']=='SOURCE_TIMESTAMP'
    assert item['counts_as_new_publication'] is False
    assert all(count==0 for count in v['counts'].values())
    assert v['collections']==views(daily(late_arrivals=[]))['collections']
    assert v['evidence_provenance']==views(daily(late_arrivals=[]))['evidence_provenance']

def test_duplicates_and_aliases_merge_stable_identity_without_losing_observation_times():
    p=daily();q=daily();p['records'][0]['doi']=q['records'][0]['doi']='10.1000/shared'
    q['records'][0].update(source_url='https://arxiv.org/abs/2610.12345v2',arxiv_id='2610.12345',source_observed_at='2026-10-19T01:00:00Z')
    q['late_arrivals'][0].update(source_url=q['records'][0]['source_url'],public_collector_observed_at=q['records'][0]['source_observed_at'],canonical_identity='arxiv:2610.12345')
    v=views(p,q);assert len(v['late_discoveries'])==1
    item=v['late_discoveries'][0];assert item['canonical_identity']=='doi:10.1000/shared'
    assert item['input_dates']==['2026-10-18','2026-10-19']
    assert len(item['observations'])==2

@pytest.mark.parametrize('url',['https://eprint.iacr.org.evil.invalid/2026/2500?token=secret',
    'https://eprint.iacr.org/2026/2500?token=secret','https://user:secret@eprint.iacr.org/2026/2500',
    'javascript:alert(1)','https://eprint.iacr.org/2026/2500#token'])
def test_untrusted_url_never_enters_supplement_or_diagnostics(url):
    p=daily();p['late_arrivals'][0]['source_url']=url;v=views(p)
    assert v['late_discoveries']==[]
    assert v['late_discovery_warnings'][0]['reason_code']=='UNTRUSTED_OR_NONCANONICAL_SOURCE_URL'
    assert url not in str(v);assert 'secret' not in str(v)

@pytest.mark.parametrize('change',[{'first_publication_time':None},{'publication_time_precision':'INVENTED'},
    {'counts_as_new_publication':True},{'row_index':True},{'canonical_identity':'eprint:2026/9999'}])
def test_corrupt_entries_are_skipped_with_safe_warning(change):
    p=daily();p['late_arrivals'][0].update(change);v=views(p)
    assert not v['late_discoveries'];assert v['late_discovery_warnings']

def test_date_only_source_precision_is_preserved_without_midnight_invention():
    p=daily();p['records'][0]['publication_timestamp']='2026-10-15'
    p['late_arrivals'][0].update(first_publication_time='2026-10-15',publication_time_precision='DATE_ONLY')
    item=views(p)['late_discoveries'][0]
    assert item['first_publication_time']=='2026-10-15';assert item['publication_time_precision']=='DATE_ONLY'

def test_existing_counted_alias_is_not_a_second_paper():
    p=daily();q=daily(late_arrivals=[]);p['records'][0]['doi']=q['records'][0]['doi']='10.1000/shared'
    q['publication_event_ledger']['collections']={'primary_publication_events':[
        {'event_id':'core','canonical_identity':'doi:10.1000/shared','row_index':0}]}
    v=views(p,q);assert v['counts']['primary_publication_events']==1;assert not v['late_discoveries']
    assert v['late_discovery_warnings'][0]['reason_code']=='ALREADY_REPRESENTED_BY_COUNTED_EVENT'


def test_untrusted_input_event_identifier_cannot_leak_to_public_view():
    from lattice_digest.publication_events import event_id
    p=daily();p['late_arrivals'][0]['event_id']='CANARY_PRIVATE_GMAIL_ID_AND_TRACKING_DATA'
    v=views(p);item=v['late_discoveries'][0]
    assert 'CANARY_PRIVATE_GMAIL_ID_AND_TRACKING_DATA' not in str(v)
    assert item['source_daily_event_id']==event_id('eprint:2026/2500','LATE_DISCOVERY',p['records'][0]['publication_timestamp'])


@pytest.mark.parametrize('blocked',[False,True])
def test_daily_pass_does_not_authorize_nonlattice_or_blocked_late_row(blocked):
    p=daily()
    if blocked:p['records'][0]['publication_event_blockers']=['UNVERIFIED_SOURCE']
    else:
        p['records'][0].update(title='Bilinear-group threshold signatures',abstract='We construct threshold signatures from bilinear pairings under the DBDH assumption.')
        p['late_arrivals'][0]['title']=p['records'][0]['title']
    v=views(p)
    assert not v['late_discoveries']
    assert v['late_discovery_warnings'][0]['reason_code']=='UNQUALIFIED_SCIENTIFIC_SOURCE'

def test_legacy_absence_mixed_schema_and_unverified_input_do_not_upgrade_evidence():
    old=daily(late_arrivals=[]);old['metadata']['publication_policy_version']=LEGACY_POLICY_VERSION
    assert 'late_discoveries' not in views(old)
    assert len(views(old,daily())['late_discoveries'])==1
    p=daily();p['_daily_input_quality']['semantic_status']='FAIL';v=views(p)
    assert not v['late_discoveries'];assert v['late_discovery_warnings'][0]['reason_code']=='UNVERIFIED_DAILY_LATE_SUPPLEMENT'

def test_conflicting_publication_evidence_has_explicit_warning():
    p=daily();q=daily();q['records'][0]['publication_timestamp']='2026-10-16'
    q['late_arrivals'][0].update(first_publication_time='2026-10-16',publication_time_precision='DATE_ONLY')
    v=views(p,q);assert len(v['late_discoveries'])==1
    assert v['late_discovery_warnings'][0]['reason_code']=='CONFLICTING_LATE_PUBLICATION_EVIDENCE'

def test_corrupt_empty_container_warns_and_renderer_defends_stored_view_url():
    v=views(daily(late_arrivals={}))
    assert v['late_discovery_warnings'][0]['reason_code']=='INVALID_DAILY_LATE_CONTAINER'
    text='\n'.join(period_late_markdown({'late_discoveries':[{'title':'malicious',
        'source_url':'https://evil.invalid?secret=token','counts_as_new_publication':False}]}))
    assert 'evil.invalid' not in text;assert 'token' not in text

def test_markdown_supplement_escapes_untrusted_title_and_avoids_raw_diagnostics():
    p=daily();title='<script>x</script> [read](https://evil.invalid)'
    p['records'][0]['title']=p['late_arrivals'][0]['title']=title
    text='\n'.join(period_late_markdown(views(p)))
    assert '<script>' not in text;assert '[read](' not in text
    assert '&lt;script&gt;' in text;assert '不计入本期出版事件' in text

@pytest.mark.parametrize('kind',['weekly','monthly'])
def test_both_real_renderers_include_additive_reading_section_without_count_changes(tmp_path,kind):
    if kind=='weekly':
        from lattice_digest.weekly_synthesis import build_weekly_synthesis,render_markdown
        payload=build_weekly_synthesis(tmp_path,date(2026,10,12),date(2026,10,18))
    else:
        from lattice_digest.monthly_synthesis import build_monthly_synthesis,render_markdown
        payload=build_monthly_synthesis(tmp_path,'2026-09')
    before=deepcopy(payload);payload['publication_event_views']=views(daily())
    text=render_markdown(payload)
    assert '迟到发现阅读补充（不计入本期出版事件）' in text
    assert 'https://eprint.iacr.org/2026/2500' in text
    payload['publication_event_views']=before['publication_event_views'];assert payload==before
