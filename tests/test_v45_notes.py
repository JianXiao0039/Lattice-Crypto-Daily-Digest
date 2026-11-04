"""TEST_ONLY note-local identities and event authorization; not proof validation."""
from lattice_digest.publication_events import source_correction_events, build_event_ledger

META={'target_date':'2026-11-04','coverage_start':'2026-11-02T13:07:43.688654+00:00','coverage_end':'2026-11-04T01:07:43.688654+00:00'}
OCT='Additional note October 7/26: The proof of Lemma 3 has been clarified.'
NOV='Additional note November 3/26: The note mentioned above has been updated with edits for greater clarity. The paper has also been reformatted.'
def test_appending_note_keeps_old_note_local_fingerprint():
    row={'abstract':OCT,'source_url':'https://eprint.iacr.org/2026/1591'}
    before=source_correction_events(row)[0]
    after=source_correction_events({**row,'abstract':OCT+' '+NOV})[0]
    assert before['source_excerpt']==after['source_excerpt']
    assert before['note_fingerprint']==after['note_fingerprint']
    assert before['source_sha256']!=after['source_sha256']

def test_november_clarity_is_not_substantive_proof_revision():
    note=source_correction_events({'abstract':NOV,'source_url':'https://eprint.iacr.org/2026/1591'})[0]
    assert note['substance_state']=='CLARIFICATION_OR_FORMATTING'
    assert note['substantive_change_verified'] is False

import hashlib
from copy import deepcopy
from tests.test_scientific_publication_p0 import record

def critical(**kw):
    return record(publication_timestamp='2025-01-01T00:00:00Z',security_impact_severity='CRITICAL',**kw).model_dump()

def test_date_note_is_noncounting_but_watch_remains():
    old=critical()
    new={**old,'abstract':old['abstract']+' '+NOV+' Rebuttal https://eprint.iacr.org/2026/1693.'}
    ledger=build_event_ledger([new],META,[old])
    assert ledger['counts']['primary_new']==ledger['counts']['event_count']==0
    watch=ledger['critical_watch'][0]
    assert watch['watch_state']=='CONTESTED_HIGH_IMPACT_LATTICE_SECURITY_CLAIM'
    assert watch['related_public_claims'][0]['mathematical_verification']=='TODO_VERIFY_NOT_EXECUTED'
    assert watch['source_revision_observations'][0]['source_time_evidence']['containment_proven'] is False
    assert new['security_impact_severity']=='CRITICAL'

def test_observed_timestamp_cannot_count_old_security_claim():
    row=critical(first_seen_at='2026-11-03T12:00:00Z')
    assert build_event_ledger([row],META)['counts']['selected']==0
    assert len(build_event_ledger([row],META)['critical_watch'])==1

def test_true_source_bound_substantive_revision_can_count_once():
    old=critical()
    abstract=old['abstract']+' A corrected proof of Lemma 3 is provided.'
    event={'event_kind':'AUTHORITATIVE_CONTENT_REVISION','change_date':'2026-11-03T12:00:00Z',
        'source_url':old['source_url'],'source_excerpt':'A corrected proof of Lemma 3 is provided.',
        'source_sha256':hashlib.sha256(abstract.encode()).hexdigest(),'evidence_state':'INDEPENDENTLY_VERIFIED',
        'substance_state':'SUBSTANTIVE_PROOF_REVISION','substantive_change_verified':True,
        'substance_evidence_url':old['source_url']}
    new={**old,'abstract':abstract,'critical_verification_events':[event]}
    ledger=build_event_ledger([new],META,[old])
    assert len(ledger['collections']['new_critical_verify_events'])==1
    assert ledger['decisions'][0]['source_time_evidence']['containment_proven'] is True
    assert build_event_ledger([new],META,[new])['counts']['selected']==0
    invalid=deepcopy(new);invalid['critical_verification_events'][0]['source_sha256']='f'*64
    assert build_event_ledger([invalid],META,[old])['counts']['selected']==0

def test_layout_only_and_later_note_cannot_reopen_prior_substance():
    before={'abstract':OCT,'source_url':'https://eprint.iacr.org/2026/1591'}
    after={**before,'abstract':OCT.replace('proof','**proof**')+' '+NOV}
    assert source_correction_events(before)[0]['note_fingerprint']==source_correction_events(after)[0]['note_fingerprint']
    old=critical(); event={'event_kind':'AUTHORITATIVE_CONTENT_REVISION','change_date':'2026-11-03T12:00:00Z',
       'source_url':old['source_url'],'source_excerpt':'Corrected proof.',
       'source_sha256':hashlib.sha256((old['abstract']+' Corrected proof.').encode()).hexdigest(),
       'evidence_state':'INDEPENDENTLY_VERIFIED','substance_state':'SUBSTANTIVE_PROOF_REVISION',
       'substantive_change_verified':True,'substance_evidence_url':old['source_url']}
    previous={**old,'abstract':old['abstract']+' Corrected proof.','critical_verification_events':[event]}
    revised={**previous,'abstract':previous['abstract']+' '+NOV,
        'critical_verification_events':[{**event,'source_sha256':hashlib.sha256((previous['abstract']+' '+NOV).encode()).hexdigest()}]}
    assert build_event_ledger([revised],META,[previous])['counts']['selected']==0

def test_october_change_does_not_change_separate_november_note_identity():
    before={'abstract':OCT+' '+NOV,'source_url':'https://eprint.iacr.org/2026/1591'}
    after={**before,'abstract':OCT.replace('clarified','substantially corrected')+' '+NOV}
    a,b=source_correction_events(before),source_correction_events(after)
    assert a[0]['note_fingerprint']!=b[0]['note_fingerprint']
    assert a[1]['note_identity']==b[1]['note_identity']
    assert a[1]['note_fingerprint']==b[1]['note_fingerprint']


def test_math_operators_and_subscripts_change_note_fingerprint():
    for math in [r'x*y', r'x__i__', r'$x*y$', r'$x__i__$', r'\(x*y\)', r'\[x__i__\]', r'$$x__i__$$']:
        row={'abstract':'Additional note October 7/26: Corrected proof '+math+'.',
             'source_url':'https://eprint.iacr.org/2026/1591'}
        altered={**row,'abstract':row['abstract'].replace('*','').replace('_','')}
        before=source_correction_events(row)[0]
        after=source_correction_events(altered)[0]
        assert math in before['source_excerpt']
        assert before['note_fingerprint']!=after['note_fingerprint']


def test_source_assertion_cannot_self_authorize_substantive_security_change():
    old=critical(); abstract=old['abstract']+' Corrected proof.'
    event={'event_kind':'AUTHORITATIVE_CONTENT_REVISION','change_date':'2026-11-03T12:00:00Z',
        'source_url':old['source_url'],'source_excerpt':'Corrected proof.',
        'source_sha256':hashlib.sha256(abstract.encode()).hexdigest(),'evidence_state':'SOURCE_ASSERTED',
        'substance_state':'SUBSTANTIVE_PROOF_REVISION','substantive_change_verified':True,
        'substance_evidence_url':old['source_url']}
    assert build_event_ledger([{**old,'abstract':abstract,'critical_verification_events':[event]}],META,[old])['counts']['selected']==0


def test_substantive_boolean_cannot_bypass_genuine_revision_guard():
    old=critical();new={**old,'abstract':old['abstract']+' '+NOV,
        'update_timestamp':'2026-11-03T12:00:00Z',
        'update_date_kind':'AUTHORITATIVE_CONTENT_REVISION_DATE',
        'critical_verification_events':[{'substantive_change_verified':True,'substance_state':'SUBSTANTIVE_PROOF_REVISION'}]}
    assert build_event_ledger([new],META,[old])['counts']['selected']==0


def test_critical_layout_change_without_dated_notes_cannot_count():
    old=critical();new={**old,'abstract':old['abstract']+'  ',
        'update_timestamp':'2026-11-03T12:00:00Z',
        'update_date_kind':'AUTHORITATIVE_CONTENT_REVISION_DATE'}
    assert build_event_ledger([new],META,[old])['counts']['selected']==0
    # Even a real text delta is a watch until substance evidence closes.
    new['abstract'] += ' Clarified exposition.'
    assert build_event_ledger([new],META,[old])['counts']['selected']==0
