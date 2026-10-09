from copy import deepcopy
from datetime import date, datetime
import json
from pathlib import Path

import pytest

from lattice_digest.authority import configured_sources, semantic_qa
from lattice_digest.evidence_contract import bind_source_evidence, score_to_label, evidence_quality_issues
from lattice_digest.models import make_paper_record
from lattice_digest.publication_events import build_event_ledger, CORE_EVENTS, period_views
from lattice_digest.scientific_daily import render_scientific_daily
from lattice_digest.scientific_scope import evaluate_scope
from lattice_digest.storage import build_daily_payload, publish_daily_pair
from lattice_digest.weekly_synthesis import aggregate_records as weekly
from lattice_digest.monthly_synthesis import aggregate_records as monthly

DAY=date(2026,10,9)
META={'target_date':str(DAY),'coverage_start':'2026-10-07T21:00:00+08:00',
      'coverage_end':'2026-10-09T09:00:00+08:00','run_mode':'backfill'}
CANARIES=json.loads((Path(__file__).parent/'fixtures/scientific_publication_p0_canaries.json').read_text(encoding='utf-8'))


def record(**kwargs):
    fields={'title':'ML-KEM implementation security','abstract':'We study side-channel leakage of ML-KEM.',
        'source':'arxiv','source_url':'https://arxiv.org/abs/2610.10000v1','arxiv_id':'2610.10000v1',
        'publication_date':'2026-10-08','publication_timestamp':'2026-10-08T00:00:00Z'}
    return bind_source_evidence(make_paper_record(**(fields|kwargs)))


def health():
    return [{'source':s['name'],'health_status':'green','runtime_state':'complete',
             'query_groups_total':1,'query_groups_success':1} for s in configured_sources() if s.get('enabled')]


@pytest.mark.parametrize('fixture',CANARIES,ids=[f['source_record']['title'] for f in CANARIES])
def test_real_scientific_controls(fixture):
    row=bind_source_evidence(make_paper_record(**fixture['source_record']))
    assert row.lattice_relevance_qualified is fixture['expected_qualified']
    assert row.relevance_label==score_to_label(row.relevance_score)
    assert (row.relevance_score>=60) is fixture['expected_qualified']
    for relation in row.source_relation_roles:
        assert relation['source_excerpt'] in getattr(row,relation['source_field'])
        assert relation['source_sha256'] and relation['evidence_status']=='SOURCE_SPAN_MODEL_INTERPRETATION'
    assert fixture['review_status']=='CODEX_SOURCE_REVIEW_NOT_HUMAN_GOLD'


def test_historical_library_is_observable_but_never_daily_selected(tmp_path):
    rows=[record(arxiv_id=f'2501.{i:05}v2',source_url=f'https://arxiv.org/abs/2501.{i:05}v2',
                 publication_date='2025-01-01',publication_timestamp=None,update_date='2025-02-01') for i in range(300)]
    p=build_daily_payload(rows,tmp_path/'data',DAY,health(),metadata=META)
    assert len(p['records'])==300
    assert p['metadata']['selection_counts']['selected']==0
    assert len(p['publication_event_ledger']['collections']['historical_library_observations'])==300
    md=render_scientific_daily(p)
    assert '<!-- event:' not in md and '300' in md
    assert semantic_qa(p,md,candidate=True)['status']=='PASS'


def test_real_rfc2822_timestamp_is_an_event():
    r=record(publication_timestamp='Wed, 07 Oct 2026 18:13:27 +0000').model_dump()
    assert build_event_ledger([r],META)['counts']['primary_new']==1


def test_unchanged_overlapping_window_is_not_promoted_again():
    r=record().model_dump()
    ledger=build_event_ledger([r],META,[r])
    assert ledger['counts']['selected']==0
    assert ledger['counts']['historical_observations']==1


def test_old_unseen_v2_cannot_claim_recent_revision():
    r=record(arxiv_id='2501.10000v2',source_url='https://arxiv.org/abs/2501.10000v2',
        publication_timestamp='2025-01-01T00:00:00Z',update_timestamp='2025-02-01T00:00:00Z').model_dump()
    assert build_event_ledger([r],META)['counts']['selected']==0


def test_genuine_revision_retains_source_version_event():
    old=record(publication_timestamp='2025-01-01T00:00:00Z',update_timestamp='2025-01-01T00:00:00Z').model_dump()
    new=record(arxiv_id='2610.10000v2',source_url='https://arxiv.org/abs/2610.10000v2',
        publication_timestamp='2025-01-01T00:00:00Z',update_timestamp='2026-10-08T00:00:00Z',
        abstract='We study new countermeasures for ML-KEM side-channel leakage.').model_dump()
    ledger=build_event_ledger([new],META,[old])
    assert ledger['counts']['primary_new']==0
    assert ledger['counts']['selected']==1
    assert ledger['collections']['revision_events'][0]['source_version']=='v2'


@pytest.mark.parametrize('date_value',['2027','2027-01','2027-01-01T00:00:00Z'])
def test_future_or_incomplete_publication_date_preserves_uncertainty(date_value):
    r=record(publication_date=date_value,publication_timestamp=None).model_dump()
    ledger=build_event_ledger([r],META)
    assert ledger['counts']['selected']==0
    assert ledger['decisions'][0]['reason'].startswith('DATE_UNCERTAIN')


def test_future_proceedings_year_does_not_hide_real_preprint():
    r=record(publication_date='2027',publication_timestamp=None,proceedings_year=2027,
        preprint_first_posted_at='2026-10-08T00:00:00Z').model_dump()
    assert build_event_ledger([r],META)['counts']['primary_new']==1


def test_old_critical_watch_remains_visible_without_reopening():
    r=record(publication_timestamp='2025-01-01T00:00:00Z',security_impact_severity='CRITICAL',
        first_seen_at='2026-10-08T00:00:00Z').model_dump()
    first=build_event_ledger([r],META)
    assert first['counts']['primary_new']==0
    assert len(first['collections']['new_critical_verify_events'])==1
    again=build_event_ledger([r],META,[r])
    assert again['counts']['selected']==0
    assert again['critical_watch'][0]['proof_verification_status']=='TODO_VERIFY'
    assert again['critical_watch'][0]['reopened'] is False


def test_new_verification_event_on_unchanged_old_paper_is_preserved():
    old=record(publication_timestamp='2025-01-01T00:00:00Z',security_impact_severity='CRITICAL').model_dump()
    new=deepcopy(old)
    new['critical_verification_events']=[{'event_kind':'SOURCE_CORRECTION','change_date':'2026-10-08T00:00:00Z',
        'source_url':'https://arxiv.org/abs/2610.10000v1','source_excerpt':'Correction to parameter claim.',
        'source_sha256':'f'*64,'evidence_state':'SOURCE_ASSERTED'}]
    ledger=build_event_ledger([new],META,[old])
    assert len(ledger['collections']['new_critical_verify_events'])==1
    assert build_event_ledger([new],META,[new])['counts']['selected']==0


def test_source_generated_conclusions_and_neighbors_cannot_promote():
    r=record(title='HQC performance',abstract='We implement HQC and compare with ML-KEM.',
             conclusion='We break Module-LWE.',ontology_neighbor_tags=['FND.MLWE'])
    assert r.relevance_score<=59
    assert any(e['role']=='COMPARISON_BASELINE' for e in r.source_relation_roles)
    assert not any(e['technical_target']=='Module-LWE' for e in r.source_relation_roles)


def test_semantic_gate_rejects_unsupported_ab_even_for_legacy_label():
    r=record(title='HQC performance',abstract='We compare HQC with ML-KEM.')
    r=r.model_copy(update={'relevance_label':'A','relevance_score':90,'evidence_policy_version':''})
    assert 'UNSUPPORTED_LATTICE_AB_CLASSIFICATION' in evidence_quality_issues(r)


def test_display_budget_does_not_truncate_qualifying_events(tmp_path):
    rows=[record(arxiv_id=f'2610.{i:05}v1',source_url=f'https://arxiv.org/abs/2610.{i:05}v1') for i in range(23)]
    p=build_daily_payload(rows,tmp_path/'data',DAY,health(),metadata=META|{'daily_priority_display_budget':3})
    md=render_scientific_daily(p)
    assert p['metadata']['selection_counts']['selected']==23
    assert md.count('<!-- event:')==23
    assert md.count('  - 原始摘要：')==3
    assert semantic_qa(p,md,candidate=True)['status']=='PASS'


@pytest.mark.parametrize('mutation',['counts','ledger','row','markdown','repeated_event'])
def test_machine_qa_rejects_unexplainable_count_or_render_discrepancy(tmp_path,mutation):
    p=build_daily_payload([record()],tmp_path/'data',DAY,health(),metadata=META)
    md=render_scientific_daily(p)
    if mutation=='counts':p['metadata']['selection_counts']['selected']=99
    elif mutation=='ledger':p['publication_event_ledger']['collections']['primary_publication_events']=[]
    elif mutation=='row':p['records'][0]['publication_event_type']='historical_library_observations'
    elif mutation=='markdown':md=md.replace('Daily publication events：1','Daily publication events：99')
    else:md+='\n<!-- event:'+p['records'][0]['publication_event_id']+' -->'
    assert semantic_qa(p,md,candidate=True)['status']=='FAIL'


def test_weekly_monthly_input_is_only_events_and_deduplicates_overlap(tmp_path):
    old=record(arxiv_id='2501.99999',publication_timestamp='2025-01-01T00:00:00Z')
    p=build_daily_payload([record(),old],tmp_path/'data',DAY,health(),metadata=META)
    loaded=[(DAY,p),(DAY,p)]
    assert len(weekly(loaded))==len(monthly(loaded))==1
    assert period_views(loaded)['counts']['primary_publication_events']==1
    p['_daily_input_quality']={'semantic_status':'FAIL'}
    assert not weekly([(DAY,p)]) and not monthly([(DAY,p)])


def test_durable_pair_and_semantic_quality_share_event_ledger(tmp_path):
    jp,mp=publish_daily_pair([record()],tmp_path,DAY,source_health=health(),metadata=META)
    p=json.loads(jp.read_text(encoding='utf-8'));md=mp.read_text(encoding='utf-8')
    assert p['metadata']['selection_counts']['event_count']==1
    assert semantic_qa(p,md)['status']=='PASS'
    assert 'NO_ACTIONABLE_RESEARCH_IDEA_FROM_CURRENT_EVIDENCE' in md
    assert 'workshop' not in md


def test_source_dated_critical_correction_reopens_only_once():
    from lattice_digest.publication_events import source_correction_events
    old=record(publication_timestamp='2025-01-01T00:00:00Z',security_impact_severity='CRITICAL').model_dump()
    new={**old,'abstract':old['abstract']+' Additional note October 8/26: The preprint has been updated with a correction to the proof of Lemma 3.'}
    events=source_correction_events(new)
    assert events[0]['date_precision']=='DATE_ONLY_SOURCE_NOTE'
    assert events[0]['source_excerpt'] in new['abstract']
    assert build_event_ledger([new],META,[old])['counts']['selected']==1
    assert build_event_ledger([new],META,[new])['counts']['selected']==0


def test_sqlite_keeps_previously_discovered_identities(tmp_path):
    import sqlite3
    from lattice_digest.storage import write_sqlite
    path=tmp_path/'library.db'
    write_sqlite([record(arxiv_id='2501.00001',source_url='https://arxiv.org/abs/2501.00001')],path)
    write_sqlite([record()],path)
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM papers').fetchone()[0]==2


def test_same_paper_source_aliases_are_one_primary_event():
    first=record().model_dump()
    alias={**first,'doi':'10.1234/example','source_url':'https://doi.org/10.1234/example'}
    ledger=build_event_ledger([first,alias],META)
    assert ledger['counts']['primary_new']==1
    assert ledger['counts']['observations']==2
    assert ledger['counts']['qualified_lattice_identities']==1
    assert ledger['decisions'][1]['collection']=='historical_library_observations'
    assert ledger['decisions'][0]['event_id']!=ledger['decisions'][1]['event_id']


def test_critical_source_url_alias_does_not_reopen_evidence():
    row=record(publication_timestamp='2025-01-01T00:00:00Z',security_impact_severity='CRITICAL').model_dump()
    change={'event_kind':'SOURCE_CORRECTION','change_date':'2026-10-08',
        'source_url':row['source_url'],'source_excerpt':'Synthetic correction evidence.',
        'source_sha256':'f'*64,'evidence_state':'SOURCE_ASSERTED'}
    old={**row,'critical_verification_events':[change]}
    new={**old,'critical_verification_events':[{**change,'source_url':'https://doi.org/10.1234/example'}]}
    assert build_event_ledger([new],META,[old])['counts']['selected']==0


def test_missing_source_cannot_count_as_qualified_identity():
    row=record(source_url='').model_dump()
    ledger=build_event_ledger([row],META)
    assert ledger['counts']['qualified_lattice_identities']==0
    assert ledger['counts']['selected']==0


def test_semantic_gate_rejects_forged_primary_flag(tmp_path):
    p=build_daily_payload([record(publication_timestamp='2025-01-01T00:00:00Z')],tmp_path/'data',DAY,health(),metadata=META)
    p['records'][0]['primary_today_new_eligible']=True
    assert semantic_qa(p,render_scientific_daily(p),candidate=True)['status']=='FAIL'


def test_semantic_gate_fails_closed_on_incomplete_count_contract(tmp_path):
    p=build_daily_payload([record()],tmp_path/'data',DAY,health(),metadata=META)
    del p['publication_event_ledger']['counts']['event_count']
    from lattice_digest.publication_events import ledger_issues
    assert ledger_issues(p)==['PUBLICATION_EVENT_LEDGER_INVALID']


def test_generic_noncrypto_fresh_observation_cannot_be_background_update():
    row=record(title='Weather prediction',abstract='We predict rain.',source_url='https://example.org/weather').model_dump()
    assert build_event_ledger([row],META)['counts']['background_updates']==0


@pytest.mark.parametrize('line',['Historical observations（档案人口，非 Daily 入选）','Background updates','A/B/C/D event classification','Recommendation action partition'])
def test_all_displayed_partitions_are_machine_checked(tmp_path,line):
    p=build_daily_payload([record()],tmp_path/'data',DAY,health(),metadata=META)
    md=render_scientific_daily(p)
    md=md.replace('- '+line+'：','- '+line+'：FORGED')
    assert semantic_qa(p,md,candidate=True)['status']=='FAIL'


def test_weekly_does_not_regenerate_generic_project_ideas(tmp_path):
    from lattice_digest.weekly_synthesis import _report_bucket_map,_idea_candidates,_paper_plan_candidates
    p=build_daily_payload([record(abstract='We study Module-SIS chameleon hashes.')],tmp_path/'data',DAY,health(),metadata=META)
    rows=weekly([(DAY,p)])
    assert len(rows)==1
    assert not _idea_candidates(rows) and not _paper_plan_candidates(rows)


@pytest.mark.parametrize('title,abstract',[
    ('ML-KEM side-channel leakage','We study ML-KEM leakage. Related work mentions TFHE, neural lattice reduction, and Gaussian sampling.'),
    ('Adelic reduction of module lattices','We develop reduction of module lattices. Related work mentions ML-KEM, TFHE, and ML-DSA.')])
def test_related_work_cannot_become_direct_research_relationship(title,abstract):
    from lattice_digest.evidence_contract import source_topics
    r=record(title=title,abstract=abstract)
    topics=source_topics(r)
    assert 'FHE' not in topics and 'Sampling' not in topics and 'AI4Lattice' not in topics
    if title.startswith('Adelic'):
        assert 'ML-KEM' not in topics and 'ML-DSA' not in topics


def test_source_role_blocker_keeps_observation_but_prevents_publication(tmp_path):
    r=record(abstract='',publication_event_blockers=['LOW_EVIDENCE_ENRICHMENT_ONLY_REJECTED'])
    p=build_daily_payload([r],tmp_path/'data',DAY,health(),metadata=META)
    assert len(p['records'])==1 and p['metadata']['selection_counts']['selected']==0
    assert 'SOURCE_ROLE_POLICY' in p['records'][0]['publication_event_reason']


def test_source_role_policy_handoff_to_event_gate(tmp_path):
    from lattice_digest.run import _filter_by_source_role
    from lattice_digest.sources.base import FetchContext
    context=FetchContext(root=tmp_path,since=datetime(2026,10,7),dry_run=True,cache_dir=tmp_path/'cache')
    configs=[{'name':'crossref','source_roles':['METADATA_ENRICHMENT','IDENTIFIER_RESOLUTION'],'standalone_no_abstract_min_relevance_score':101}]
    r=record(abstract='',source='crossref')
    kept,dropped=_filter_by_source_role([r],configs,context)
    assert dropped==[r] and not kept
    blocked=r.model_copy(update={'publication_event_blockers':['LOW_EVIDENCE_ENRICHMENT_ONLY_REJECTED']})
    assert build_event_ledger([blocked.model_dump()],META)['counts']['selected']==0



def test_generic_proof_assumption_is_not_primary_lattice_object():
    r=record(title='A generic trapdoor-function impossibility theorem',
        abstract='Assuming standard LWE and indistinguishability obfuscation, every efficient hash family admits a counterexample trapdoor function.')
    assert not r.lattice_relevance_qualified and r.relevance_score<60
    assert any(e['role']=='LATTICE_HARDNESS_ASSUMPTION' for e in r.source_relation_roles)


def test_concrete_lattice_construction_from_assumption_is_preserved():
    r=record(title='An anonymous identity-based broadcast construction',
        abstract='We construct identity-based anonymous broadcast encryption under the LWE assumption.')
    assert r.lattice_relevance_qualified and r.relevance_score>=80



def test_nonprimary_generic_assumption_does_not_gain_direct_topic_from_other_object():
    from lattice_digest.evidence_contract import source_topics
    r=record(title='BKZ lattice reduction',abstract='We study BKZ lattice reduction. Assuming LWE, a generic obfuscation lemma follows.')
    assert r.lattice_relevance_qualified
    assert 'LWE' not in source_topics(r)
    assert all(not e['qualifies_lattice_scope'] for e in r.source_relation_roles if e['role']=='LATTICE_HARDNESS_ASSUMPTION')



def test_generic_pqc_without_lattice_evidence_is_observable_not_daily_background():
    r=record(title='Enterprise quantum-safe security',abstract='We study generic post-quantum security.')
    ledger=build_event_ledger([r.model_dump()],META)
    assert ledger['counts']['observations']==1 and ledger['counts']['background_updates']==0


def test_physical_security_with_explicit_crypto_context_remains_qualified():
    r=record(title='ML-KEM side-channel leakage',abstract='We study side-channel leakage of ML-KEM on hardware with phonon noise.')
    assert r.lattice_relevance_qualified



@pytest.mark.parametrize('caller_primary',[False,True])
def test_first_posted_in_window_v2_is_valid_primary_and_publishable(tmp_path,caller_primary):
    r=record(arxiv_id='2610.20001v2',source_url='https://arxiv.org/abs/2610.20001v2',
        update_timestamp='2026-10-08T10:00:00Z',primary_today_new_eligible=caller_primary)
    jp,mp=publish_daily_pair([r],tmp_path,DAY,source_health=health(),metadata=META)
    p=json.loads(jp.read_text(encoding='utf-8'))
    assert p['metadata']['selection_counts']['primary_new']==1
    assert p['metadata']['cross_day_qa']['status']=='PASS'
    assert p['records'][0]['publication_event_type']=='primary_publication_events'
    assert semantic_qa(p,mp.read_text(encoding='utf-8'))['status']=='PASS'
