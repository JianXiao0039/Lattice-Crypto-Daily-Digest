"""Independent gate checks using preserved incident rows, not fabricated papers.

The loader is mocked only at its independently tested resource boundary. The
source-bound rows supplied by that boundary must prevail over saved evidence.
The explicitly injected revision below is an adversarial test, not a paper fact.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

import pytest

from lattice_digest.publication_events import build_event_ledger
from lattice_digest.report_gate import GateError, verify


DOI = '10.21203/rs.3.rs-11270790/v1'


@pytest.fixture
def incident():
    # Acceptance explicitly supplies the preserved canonical workspace.
    # Ordinary portable CI without the private forensic input skips;
    # these tests are executed with the actual incident files during acceptance.
    root = Path(os.environ.get('V41_ORIGINAL_ROOT', str(Path(__file__).resolve().parents[4])))
    current = root / 'data/2026/daily/2026-10-27.json'
    previous = root / 'data/2026/daily/2026-10-26.json'
    markdown = root / 'digests/2026/daily/2026-10-27.md'
    if not all(p.is_file() for p in (current, previous, markdown)):
        pytest.skip('preserved October 27 forensic input is unavailable')
    payload = json.loads(current.read_bytes())
    history = json.loads(previous.read_bytes())
    row = next(r for r in payload['records'] if str(r.get('doi') or '').lower() == DOI)
    prior = next(r for r in history['records'] if str(r.get('doi') or '').lower() == DOI)
    assert len(previous.read_bytes()) == 33_998_116
    assert hashlib.sha256(previous.read_bytes()).hexdigest() == '57ce85cb8cc85b0a5ea9fe75d0b65b34f11a988914e210f5d33b5c30317647e5'
    return deepcopy(payload['metadata']), deepcopy(row), deepcopy(prior), markdown.read_bytes()


def candidate_pair(root, metadata, row, saved_prior, markdown):
    ledger = build_event_ledger([row], metadata, saved_prior)
    decision = ledger['decisions'][0]
    row.update(publication_event_type=decision['collection'], publication_event_id=decision['event_id'],
               primary_today_new_eligible=decision['collection'] == 'primary_publication_events')
    metadata['selection_counts'] = ledger['counts']
    metadata['cross_day_qa'] = {'status': 'PASS', 'issues': []}
    metadata['semantic_qa'] = {'status': 'PASS', 'issues': []}
    payload = {'metadata': metadata, 'records': [row], 'publication_event_ledger': ledger,
               'publication_history_evidence': saved_prior}
    jp=root/'data/2026/daily/2026-10-27.json'
    mp=root/'digests/2026/daily/2026-10-27.md'
    jp.parent.mkdir(parents=True);mp.parent.mkdir(parents=True)
    jp.write_text(json.dumps(payload,ensure_ascii=False),'utf-8')
    mp.write_bytes(markdown)
    return decision


def history_boundary(monkeypatch, rows, *, source_hash='b'*64):
    from lattice_digest import promotion_history
    evidence = {'schema_version': 'history-evidence-v41', 'complete': True,
                'loaded': [{'date': '2026-10-26', 'sha256': source_hash}],
                'missing': [], 'unusable': [], 'days': 14}
    monkeypatch.setattr(promotion_history,'load_promotion_history',lambda *args,**kwargs:(rows,evidence))


def test_independent_gate_rejects_forged_saved_revision_projection(incident,tmp_path,monkeypatch):
    meta,row,_,markdown=incident
    # Fault injection: this timestamp is intentionally test-only. It must not be
    # mistaken for a source assertion or enter the forensic recovery artifacts.
    row.update(publication_date='2026-10-01', publication_timestamp='2026-10-01T00:00:00+00:00',
               preprint_first_posted_at=None,announcement_timestamp=None,announcement_date=None,
               update_timestamp='2026-10-26T12:00:00+00:00',update_date_kind='AUTHORITATIVE_CONTENT_REVISION_DATE')
    verified_prior={**deepcopy(row),'_history_verified':True}
    forged_prior={**deepcopy(verified_prior),'abstract':'TEST-ONLY forged previous abstract projection'}
    meta['promotion_history']={'schema_version':'history-evidence-v41','complete':True,'loaded':[]}
    decision=candidate_pair(tmp_path,meta,row,[forged_prior],markdown)
    assert decision['collection']=='revision_events'
    assert build_event_ledger([row],meta,[verified_prior])['decisions'][0]['collection']=='historical_library_observations'
    history_boundary(monkeypatch,[verified_prior])
    # Deliberately simulate an independently defective scientific evaluator that
    # returns PASS. The history-backed ownership check must remain effective.
    from lattice_digest import authority
    monkeypatch.setattr(authority,'semantic_qa',lambda *args,**kwargs:{
        'status':'PASS','derived_authority':{'authority_state':meta['authority_state']}})
    with pytest.raises(GateError) as failure:verify(tmp_path,'daily','2026-10-27')
    assert failure.value.code=='EVENT_OWNERSHIP_CONFLICT'


def test_independent_gate_catches_actual_duplicate_with_forged_pass_labels(incident,tmp_path,monkeypatch):
    meta,row,prior,markdown=incident
    meta['promotion_history']={'schema_version':'history-evidence-v41','complete':True,'loaded':[]}
    decision=candidate_pair(tmp_path,meta,row,[],markdown)
    assert decision['collection']=='primary_publication_events'
    history_boundary(monkeypatch,[{**prior,'_history_verified':True}])
    with pytest.raises(GateError) as failure:verify(tmp_path,'daily','2026-10-27')
    assert failure.value.code=='CROSS_DAY_DUPLICATE_PRIMARY'


def test_independent_gate_rejects_changed_history_source_binding(incident,tmp_path,monkeypatch):
    meta,row,prior,markdown=incident
    prior['_history_verified']=True
    meta['promotion_history']={'schema_version':'history-evidence-v41','complete':True,
        'loaded':[{'date':'2026-10-26','sha256':'a'*64}]}
    decision=candidate_pair(tmp_path,meta,row,[prior],markdown)
    assert decision['collection']=='historical_library_observations'
    history_boundary(monkeypatch,[prior],source_hash='b'*64)
    with pytest.raises(GateError) as failure:verify(tmp_path,'daily','2026-10-27')
    assert failure.value.code=='HISTORY_INDEX_SOURCE_MISMATCH'
