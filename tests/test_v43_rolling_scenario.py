"""One continuous TEST_ONLY scenario; real incident bytes anchor input provenance.

Future dates, changed identities and complete source health below are synthetic
transport controls. They are not original collection or publication evidence.
"""
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil

import pytest

from lattice_digest import history_resources, report_gate
from lattice_digest.models import PaperRecord
from lattice_digest.evidence_contract import bind_source_evidence
from lattice_digest.promotion_history import load_promotion_history, apply_promotion_history
from lattice_digest.storage import publish_daily_pair
from tests.v41_history_fixture import seed_empty_history


ROOT = Path(os.environ.get('V41_ORIGINAL_ROOT', r'D:/Code/CodexProjects/lattice-crypto-daily-digest'))


def test_continuous_sixteen_day_incident_anchored_rolling_scenario(tmp_path):
    expected = {
        '2026-10-26': (33998116, '57ce85cb8cc85b0a5ea9fe75d0b65b34f11a988914e210f5d33b5c30317647e5'),
        '2026-10-30': (34790320, '089b64fd52f953ea7f73fe2a69bba86a5e7cb30f19aa3c5c8c4c59d7edc36778'),
    }
    receipts = []
    originals = {}
    for day, (size, digest) in expected.items():
        path = ROOT / f'data/2026/daily/{day}.json'
        if not path.exists():
            pytest.skip('private original incident corpus unavailable; no fabricated large input')
        raw = path.read_bytes()
        assert len(raw) == size and hashlib.sha256(raw).hexdigest() == digest
        rows, receipt = history_resources.load_verified_history_pair(ROOT/'data', date.fromisoformat(day))
        assert receipt['source_bytes'] == size and receipt['sha256'] == digest
        assert receipt['positive_event_ownership'] is False
        assert all(row['_history_positive_event_owner'] is False for row in rows)
        originals[day] = json.loads(raw)
        receipts.append(receipt)

    real = next(row for row in originals['2026-10-26']['records']
                if row.get('doi') == '10.21203/rs.3.rs-11270790/v1')
    start = date(2026, 10, 18)
    seed_empty_history(tmp_path, start)
    # Actual missing-original-evidence placeholder. Its date is unchanged.
    fixture = Path(__file__).parent/'fixtures/v43_oct17'
    for folder, ext in [('data', 'json'), ('digests', 'md')]:
        shutil.copyfile(fixture/f'2026-10-17.{ext}',
                        tmp_path/f'{folder}/2026/daily/2026-10-17.{ext}')

    def test_row(day, suffix):
        row = deepcopy(real)
        identity = f'10.99999/test-only-v43-{suffix}'
        row.update(doi=identity, arxiv_id='', eprint_id='', paper_id='doi:'+identity,
                   source_url='https://doi.org/'+identity, source_urls=[],
                   publication_date=str(day), publication_timestamp=str(day)+'T12:00:00+00:00',
                   publication_date_kind='AUTHORITATIVE_PUBLICATION_DATE',
                   preprint_first_posted_at=None, announcement_timestamp=None,
                   announcement_date=None, update_date=None, update_timestamp=None,
                   source_version_timestamp=None, critical_verification_events=[],
                   publication_event_blockers=[], security_impact_severity='NONE')
        return row

    # A source-bound failed candidate is observed in the first rolling window.
    # Its forged saved primary flag must never grant positive owner authority.
    failed_day = start-timedelta(days=2)
    failed = tmp_path/f'data/2026/daily/{failed_day}.json'
    failed_payload = json.loads(failed.read_bytes())
    failed_row = test_row(failed_day, 'failed-candidate')
    failed_row['publication_event_type'] = 'primary_publication_events'
    failed_payload['records'] = [failed_row]
    failed_payload['metadata'].update(publication_state='QA_REJECTED',
        fixture_evidence='TEST_ONLY_FAILED_CANDIDATE_NEVER_INDEPENDENTLY_ACCEPTED')
    failed.write_text(json.dumps(failed_payload), encoding='utf-8')

    first = test_row(start, 'observed-under-gap')
    last = test_row(start+timedelta(days=14), 'new-after-gap-expiry')
    base = originals['2026-10-30']['metadata']
    partial_health = originals['2026-10-30']['source_health']
    complete_health = [dict(source=name, health_status='green', runtime_state='complete')
                       for name in ('arxiv', 'iacr_eprint', 'openalex', 'semantic_scholar', 'crossref', 'dblp')]
    states = []
    for offset in range(16):
        target = start+timedelta(days=offset)
        prior, history = load_promotion_history(tmp_path/'data', target)
        assert history['complete'] is (offset >= 14)
        assert all(not row.get('_history_positive_event_owner') for row in prior)
        if offset == 0:
            assert any(row.get('doi') == failed_row['doi'] for row in prior)
            assert any(item['date'] == str(failed_day) for item in history['unusable'])
        # Gap-time attempts, duplicate observations, empty day and failed candidate
        # repetitions all occur in this same growing canonical history.
        rows = ([first] if offset in (0, 1, 4, 8, 13) else
                [failed_row] if offset == 2 else
                [test_row(target, 'new-during-gap')] if offset == 5 else
                [last] if offset in (14, 15) else [])
        partial = offset in (0, 3, 7, 15)
        meta = deepcopy(base)
        meta.update(target_date=str(target), run_date=str(target),
                    coverage_start=str(target-timedelta(days=1))+'T16:00:00+00:00',
                    coverage_end=str(target)+'T16:00:00+00:00',
                    promotion_history=history, trigger_kind='TEST_ONLY',
                    fixture_evidence='TEST_ONLY_FUTURE_DATE_IDENTITY_AND_SOURCE_STATE')
        for key in ('generation_id', 'markdown_sha256', 'semantic_qa', 'structural_qa', 'cross_day_qa'):
            meta.pop(key, None)
        records = apply_promotion_history([bind_source_evidence(PaperRecord.model_validate(
            {key: value for key, value in row.items() if key in PaperRecord.model_fields})
            ) for row in rows], prior)
        jp, _ = publish_daily_pair(records, tmp_path, target,
            source_health=partial_health if partial else complete_health,
            warnings=['TEST_ONLY simulation, not production observations'], metadata=meta)
        payload = json.loads(jp.read_bytes())
        counts = payload['publication_event_ledger']['counts']
        assert counts['primary_new'] == (1 if offset == 14 else 0)
        assert counts['event_count'] == (1 if offset == 14 else 0)
        gate = None
        if offset in (0, 3, 14, 15):
            accepted = report_gate.verify(tmp_path, 'daily', str(target))
            gate = dict(quality=accepted.quality, diagnostics=accepted.diagnostics,
                        event_count=len(accepted.events))
            assert accepted.quality == ('VERIFIED_AUTHORITATIVE' if offset == 14 else 'PROVISIONAL_PUBLIC')
        states.append(dict(date=str(target), test_only=True, history_complete=history['complete'],
            missing=history['missing'], unusable=history['unusable'], partial_sources=partial,
            input_identities=[row['doi'] for row in rows], counts=counts, gate=gate))

    assert states[13]['history_complete'] is False
    assert states[14]['history_complete'] is True
    assert sum(day['counts']['primary_new'] for day in states) == 1
    evidence_path = os.environ.get('V43_ROLLING_EVIDENCE_PATH')
    if evidence_path:
        artifact = dict(schema_version='v43-test-only-continuous-rolling-v1',
            scenario_kind='TEST_ONLY_NOT_PRODUCTION_EXECUTION', module_files={
                'history_resources': history_resources.__file__, 'report_gate': report_gate.__file__},
            real_large_source_bound_receipts=receipts, continuous_days=states,
            assertion_scope='No gap-time promotions; failed candidate no positive owner; natural expiry; one new event then duplicate veto')
        path = Path(evidence_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
