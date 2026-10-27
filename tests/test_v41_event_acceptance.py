"""Incident-backed integration checks. No Git, network, or original writes."""
from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import shutil

import pytest

from lattice_digest.publication_events import build_event_ledger, attach_events, period_views
from lattice_digest.promotion_history import classify_event, identity_keys
from lattice_digest.report_gate import verify, GateError
from lattice_digest.authority import derive_authority, semantic_qa, HISTORY_INCOMPLETE_ZERO_TEXT
from lattice_digest.models import PaperRecord
from lattice_digest.storage import build_daily_payload

ORIGINAL = Path(os.environ.get('V41_ORIGINAL_ROOT', str(Path(__file__).resolve().parents[4])))
DAY = date(2026, 10, 27)


@pytest.fixture(scope='module')
def incident():
    p = ORIGINAL / 'data/2026/daily/2026-10-27.json'
    if not p.is_file():
        pytest.skip('preserved incident input unavailable')
    current = json.loads(p.read_bytes())
    previous = json.loads((ORIGINAL / 'data/2026/daily/2026-10-26.json').read_bytes())
    return current, previous


def doi_row(payload):
    return next(r for r in payload['records'] if r.get('doi') == '10.21203/rs.3.rs-11270790/v1')


def test_exact_incident_duplicate_and_nonduplicate_candidates(incident):
    current, previous = incident
    original = build_event_ledger(current['records'], current['metadata'], current['publication_history_evidence'])
    assert original == current['publication_event_ledger']
    replay = build_event_ledger(current['records'], current['metadata'], previous['records'] + current['publication_history_evidence'])
    assert original['counts']['primary_new'] == 4
    assert replay['counts']['primary_new'] == 3  # conditional candidates, not authorized publication
    before = next(e for e in original['decisions'] if e['canonical_identity'].startswith('doi:10.21203/'))
    after = replay['decisions'][before['row_index']]
    assert before['event_id'] == 'b587afe451d8a061baab91575e388e6f8ad811b6be77702262e88fa4d412fc9c'
    assert after['collection'] == 'historical_library_observations'
    assert classify_event(doi_row(current), previous['records'])[0] in {'METADATA_ONLY_UPDATE', 'UNCHANGED_CROSS_DAY_DUPLICATE'}
    assert before['source_content_sha256'] == after['source_content_sha256']


def test_incomplete_history_cannot_authorize_three_candidates(incident):
    current, previous = incident
    meta = {**current['metadata'], 'promotion_history': {
        'schema_version': 'history-evidence-v41', 'complete': False,
        'primary_ownership_eligible': False, 'unusable': [{'date': '2026-10-17', 'code': 'HISTORY_EVIDENCE_UNUSABLE'}]}}
    ledger = build_event_ledger(current['records'], meta, previous['records'])
    assert ledger['counts']['primary_new'] == 0
    assert not ledger['collections']['revision_events']
    assert sum(e['reason'].startswith('HISTORY_EVIDENCE_UNUSABLE') for e in ledger['decisions']) == 3


def test_overlap_first_publication_is_one_with_real_source(incident):
    current, previous = incident
    day26 = build_event_ledger([doi_row(previous)], previous['metadata'])
    day27 = build_event_ledger([doi_row(current)], current['metadata'], [doi_row(previous)])
    assert day26['counts']['primary_new'] + day27['counts']['primary_new'] == 1
    loaded = [(date(2026,10,26), {'metadata': {'publication_policy_version': previous['metadata']['publication_policy_version']},
               '_daily_input_quality': {'semantic_status': 'PASS'}, 'publication_event_ledger': day26}),
              (DAY, {'metadata': {'publication_policy_version': current['metadata']['publication_policy_version']},
               '_daily_input_quality': {'semantic_status': 'PASS'}, 'publication_event_ledger': day27})]
    assert period_views(loaded)['counts']['primary_publication_events'] == 1


def test_independent_gate_rejects_real_duplicate_even_saved_qa_passes(tmp_path, incident):
    current, previous = incident
    for day in ('2026-10-26','2026-10-27'):
        for directory, extension in [('data','json'),('digests','md')]:
            destination = tmp_path / directory / '2026/daily' / (day + '.' + extension)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ORIGINAL / destination.relative_to(tmp_path), destination)
    assert current['metadata']['cross_day_qa']['status'] == 'PASS'
    with pytest.raises(GateError, match='CROSS_DAY_DUPLICATE_PRIMARY'):
        verify(tmp_path, 'daily', str(DAY))


def test_noncounting_diagnostic_never_asserts_no_news(incident, tmp_path):
    current, previous = incident
    meta = {**current['metadata'], 'promotion_history': {'schema_version': 'history-evidence-v41', 'complete': False},
            '_publication_prior': previous['records']}
    records = [PaperRecord.model_validate({k:v for k,v in r.items() if k in PaperRecord.model_fields}) for r in current['records']]
    payload = build_daily_payload(records, tmp_path/'data', DAY, current['source_health'], metadata=meta)
    from lattice_digest.scientific_daily import render_scientific_daily
    markdown = render_scientific_daily(payload)
    assert HISTORY_INCOMPLETE_ZERO_TEXT in markdown
    assert '今日未发现值得记录的格密码相关新论文。' not in markdown
    assert payload['metadata']['authority_state'] == 'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'
    assert payload['publication_event_ledger']['counts']['primary_new'] == 0


def test_unverified_prior_cannot_authorize_revision(incident):
    current, previous = incident
    old = {**doi_row(previous), '_history_verified': False}
    revised = {**doi_row(current), 'abstract': doi_row(current)['abstract']+' Source content revision.',
               'update_timestamp': '2026-10-26T20:00:00Z', 'update_date_kind': 'AUTHORITATIVE_CONTENT_REVISION_DATE'}
    ledger = build_event_ledger([revised], current['metadata'], [old])
    assert not ledger['collections']['revision_events']
