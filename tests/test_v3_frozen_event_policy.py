import copy
import hashlib
import json
from datetime import date
from pathlib import Path
import pytest
from lattice_digest.publication_events import (
    POLICY_VERSION, LEGACY_POLICY_VERSION, build_event_ledger, ledger_issues,
    normalize_period_inputs, period_event_rows, period_views,
)
from lattice_digest.evidence_contract import source_scope_score, source_topics
from lattice_digest.scientific_scope_v1 import evaluate_scope as frozen

ROW={'title':'Efficient Fixed-Point Implementation of Mitaka',
     'abstract':'The Mitaka signature scheme is a variant of Falcon. We present a fixed-point implementation of Mitaka.',
     'source':'IACR ePrint','source_url':'https://eprint.iacr.org/2026/2521',
     'eprint_id':'2026/2521','authors':[], 'relevance_label':'C','relevance_score':49,
     'publication_timestamp':'2026-10-17T12:57:50Z'}
META={'target_date':'2026-10-18','coverage_start':'2026-10-16T20:18:41Z','coverage_end':'2026-10-18T08:18:41Z'}

def payload(policy):
    meta={**META,'publication_policy_version':policy}
    ledger=build_event_ledger([ROW],meta)
    e=ledger['decisions'][0]
    row={**ROW,'publication_event_type':e['collection'],'publication_event_id':e['event_id'],
         'primary_today_new_eligible':e['collection']=='primary_publication_events'}
    return {'metadata':{**meta,'selection_counts':ledger['counts']},'records':[row],
            'publication_event_ledger':ledger,'publication_history_evidence':[]}

def test_frozen_evaluator_is_exact_pre_v3_published_source():
    p=Path(__file__).parents[1]/'src/lattice_digest/scientific_scope_v1.py'
    assert hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()=='2181f08406cbc035601c0de65d2b54f77f578f9251894e4398b60285e318df38'

def test_version_changes_are_explicit_not_silent_historical_reclassification():
    old,new=payload(LEGACY_POLICY_VERSION),payload(POLICY_VERSION)
    assert old['publication_event_ledger']['counts']['primary_new']==0
    assert new['publication_event_ledger']['counts']['primary_new']==1
    assert ledger_issues(old)==ledger_issues(new)==[]
    assert source_scope_score(ROW,scope_evaluator=frozen)[1]==49
    assert source_scope_score(ROW)[1]>=80
    assert source_topics(ROW,scope_evaluator=frozen)==[]

def test_unknown_or_mismatched_policy_fails_closed():
    with pytest.raises(ValueError,match='UNSUPPORTED_PUBLICATION_POLICY'):
        build_event_ledger([ROW],{**META,'publication_policy_version':'future-unreviewed'})
    x=payload(LEGACY_POLICY_VERSION);x['metadata']['publication_policy_version']=POLICY_VERSION
    assert 'UNSUPPORTED_OR_MISMATCHED_PUBLICATION_POLICY' in ledger_issues(x)
    x['metadata']['publication_policy_version']='future-unreviewed'
    with pytest.raises(ValueError,match='UNSUPPORTED_PUBLICATION_POLICY'):
        normalize_period_inputs([(date(2026,10,18),x)])

def test_corrupt_frozen_ledger_still_rejected():
    x=payload(LEGACY_POLICY_VERSION);x['publication_event_ledger']['counts']['primary_new']=99
    assert 'PUBLICATION_EVENT_LEDGER_MISMATCH' in ledger_issues(x)

def test_missing_policy_cannot_disguise_existing_ledger_as_legacy():
    from lattice_digest.authority import semantic_qa
    x=payload(LEGACY_POLICY_VERSION);x['metadata'].pop('publication_policy_version')
    with pytest.raises(ValueError,match='UNVERSIONED_PUBLICATION_LEDGER'):
        normalize_period_inputs([(date(2026,10,18),x)])
    assert semantic_qa(x,None,candidate=True)['status']=='FAIL'
    assert 'UNSUPPORTED_OR_MISMATCHED_PUBLICATION_POLICY' in semantic_qa(x,None,candidate=True)['issues']

def test_mixed_recognized_schemas_preserve_events_and_scores():
    old,new=payload(LEGACY_POLICY_VERSION),payload(POLICY_VERSION)
    for x in [old,new]:x['_daily_input_quality']={'semantic_status':'PASS'}
    original=copy.deepcopy([old,new]);loaded=[(date(2026,10,17),old),(date(2026,10,18),new)]
    result=normalize_period_inputs(loaded)
    assert [x for _,x in result]==original
    assert period_event_rows(old)==[]
    assert len(period_event_rows(new))==1
    assert period_views(result)['counts']['primary_publication_events']==1
    assert [r['relevance_score'] for _,x in result for r in x['records']]==[49,49]
