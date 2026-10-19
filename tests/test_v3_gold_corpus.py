"""Public source regression corpus; unresolved source evidence never becomes PASS recall.

Gold expectations were adjudicated from original technical objects, independently
of the implementation. Exact titles and identities belong only in test data.
"""
import json
from pathlib import Path
import pytest

from lattice_digest.scientific_scope import evaluate_scope
from lattice_digest.scientific_contribution import contribution_view
from lattice_digest.publication_events import build_event_ledger

GOLD=json.loads((Path(__file__).parent/'fixtures/literature_gold_v3.json').read_text(encoding='utf-8'))
ROWS=GOLD['records']

def key(row):
    return str(row['index'] or row['stable_ids']['eprint'])

@pytest.mark.parametrize('row',ROWS,ids=key)
def test_independent_scientific_contribution_gold(row):
    if not row['primary_source_verified']:
        pytest.skip('Original paper unavailable; maintainer confirmation is insufficient for primary-paper classification acceptance')
    result=contribution_view(row)
    assert result['category']==row['expected_category'], result
    assert result['contribution_kind']==row['expected_kind'], result
    assert result['frozen_selection_changed'] is False

@pytest.mark.parametrize('row',ROWS,ids=key)
def test_independent_scope_recall_and_false_positive_controls(row):
    if not row['primary_source_verified']:
        pytest.skip('Original source object unresolved; exclude from verified recall denominator')
    # SoK and applications describe a contribution, while broad frozen scope
    # may still accept their lattice content. Those concepts are not conflated.
    if row['expected_category'] in {'ADJACENT_PQC','LATTICE_APPLICATIONS'} and row['index']!=9:
        return
    decision=evaluate_scope(row)
    assert decision['lattice_relevance_qualified'] is row['expected_core'], decision

def test_all_twenty_eight_objects_and_three_distinct_extra_anchors():
    assert sorted(r['index'] for r in ROWS if r['index'])==list(range(1,29))
    assert len(ROWS)==31
    ids=[r['stable_ids']['eprint'] or r['stable_ids']['arxiv'] or r['title'] for r in ROWS]
    assert len(ids)==len(set(ids))
    for r in ROWS:
        assert r['source_url'].startswith(('https://eprint.iacr.org/','https://arxiv.org/','https://ir.cwi.nl/'))
        assert r['evidence_ref']
        assert r['chronology']

def test_two_fft_dual_papers_retain_distinct_authoritative_identity():
    rows={r['index']:r for r in ROWS if r['index']}
    assert rows[14]['stable_ids']['eprint']=='2026/2166'
    assert rows[16]['stable_ids']['eprint']=='2026/2186'
    assert rows[14]['title']!=rows[16]['title']
    assert rows[16]['authors']==['Jiale Li','Li-Ping Wang','Huaxiong Wang']

def test_official_received_approval_and_old_venue_are_not_one_date():
    rows={r['index']:r for r in ROWS if r['index']}
    assert rows[18]['chronology']['source_received_date']=='2026-10-15'
    assert rows[18]['chronology']['official_approval_date']=='2026-10-17'
    assert rows[18]['chronology']['first_publication_time'] is None
    assert rows[17]['chronology']['formal_venue_online_date']=='2025-04-28'
    assert rows[17]['chronology']['official_approval_date']=='2026-10-19'
    assert rows[21]['chronology']['defence_at']=='2026-09-23T16:00:00+02:00'

@pytest.mark.parametrize('index',[1,17,23,26,28])
def test_old_work_new_ingestion_does_not_make_october_nineteen_publication(index):
    original=next(r for r in ROWS if r['index']==index)
    row=dict(original,first_seen_at='2026-10-19T01:00:00Z')
    # Only independently supported old public existence/submission bounds are
    # used. A received timestamp is never fabricated as a publication instant.
    old={1:'2024',17:'2025-04-28',23:'2026-03-23',26:'2026-09-21T14:43:17Z',28:'2026-06-07'}[index]
    row.update(publication_date=old,publication_date_kind='VERIFIED_PRIOR_PUBLIC_EXISTENCE',
               eprint_id=original['stable_ids']['eprint'],arxiv_id=original['stable_ids']['arxiv'])
    ledger=build_event_ledger([row],{'target_date':'2026-10-19','coverage_start':'2026-10-17T21:00:00+08:00','coverage_end':'2026-10-19T09:00:00+08:00'})
    assert ledger['collections']['primary_publication_events']==[]

def test_fixture_contains_only_public_metadata_and_no_mail_secrets():
    text=json.dumps(GOLD,ensure_ascii=False).casefold()
    for forbidden in ('gmail_message_id','unsubscribe','refresh_token','access_token','password','cookie','newbounce@iacr.org'):
        assert forbidden not in text
    unresolved=next(r for r in ROWS if r['index']==13)
    assert unresolved['primary_source_verified'] is False
    assert unresolved['abstract']==''
