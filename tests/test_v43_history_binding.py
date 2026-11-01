"""Portable regression for the actual legacy-unusable-projection binding hole.

The Oct17 fixture is original byte evidence. All surrounding empty days and the
Oct18 cloud observation report are TEST_ONLY transport, with no runtime authority.
"""
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from lattice_digest import promotion_history
from lattice_digest.report_gate import verify, GateError
from lattice_digest.storage import publish_daily_pair
from tests.v41_history_fixture import seed_empty_history


def _bound_zero_report(tmp_path):
    target = date(2026, 10, 18)
    seed_empty_history(tmp_path, target)
    fixture = Path(__file__).parent/'fixtures/v43_oct17'
    for folder, ext in [('data', 'json'), ('digests', 'md')]:
        shutil.copyfile(fixture/f'2026-10-17.{ext}',
                        tmp_path/f'{folder}/2026/daily/2026-10-17.{ext}')
    metadata = dict(target_date=str(target), collector='github_actions',
        quality_status='provisional', run_mode='daily',
        coverage_start='2026-10-17T04:00:00+00:00',
        coverage_end='2026-10-18T16:00:00+00:00',
        trigger_kind='TEST_ONLY', runtime_code_authenticated='NOT_RUN',
        test_evidence='TEST_ONLY_SYNTHETIC_TRANSPORT_NO_AUTHENTICATED_RUNTIME')
    health = [dict(source=name, health_status='red', runtime_state='failed')
              for name in ('arxiv', 'iacr_eprint', 'openalex', 'semantic_scholar')]
    jp, mp = publish_daily_pair([], tmp_path, target, metadata=metadata,
        source_health=health, warnings=['TEST_ONLY, not a historical production execution'])
    return target, jp, mp


def test_unusable_history_source_projection_must_be_bound(tmp_path, monkeypatch):
    target, jp, mp = _bound_zero_report(tmp_path)
    original_json, original_markdown = jp.read_bytes(), mp.read_bytes()
    payload = json.loads(original_json)
    prior_gap = next(item for item in payload['metadata']['promotion_history']['unusable']
                     if item['date'] == '2026-10-17')
    assert prior_gap['source_receipt']['sha256'] == 'b07e74b6fdf438b6d9bafbc9c49b978e222d8b4ed6f49742179b345376cde874'
    assert prior_gap['source_receipt']['history_trust_tier'] == 'UNVERIFIED_OR_MISSING'
    accepted = verify(tmp_path, 'daily', str(target))
    assert accepted.events == [] and accepted.quality == 'PROVISIONAL_PUBLIC'
    from lattice_digest.public_report import project
    public = project(accepted)
    assert public['history_evidence']['capability'] == 'LOCAL_CANONICAL_HISTORY'
    assert public['history_evidence']['history_complete'] is False

    # Original V4.1/V4.2 failed reports had precisely this unbound unusable shape.
    # Daily has no self-JSON hash, so only history projection validation catches it.
    del prior_gap['source_receipt']['sha256']
    jp.write_text(json.dumps(payload), encoding='utf-8')
    assert mp.read_bytes() == original_markdown
    with pytest.raises(GateError) as failure:
        verify(tmp_path, 'daily', str(target))
    assert failure.value.code == 'HISTORY_PROJECTION_UNBOUND'

    jp.write_bytes(original_json)
    actual_loader = promotion_history.load_promotion_history

    def changed_fresh_source_receipt(*args, **kwargs):
        rows, history = actual_loader(*args, **kwargs)
        history = deepcopy(history)
        gap = next(item for item in history['unusable'] if item['date'] == '2026-10-17')
        gap['source_receipt']['sha256'] = '0'*64
        return rows, history

    monkeypatch.setattr(promotion_history, 'load_promotion_history', changed_fresh_source_receipt)
    with pytest.raises(GateError) as failure:
        verify(tmp_path, 'daily', str(target))
    assert failure.value.code == 'HISTORY_INDEX_SOURCE_MISMATCH'
    monkeypatch.setattr(promotion_history, 'load_promotion_history', actual_loader)
    rebound = verify(tmp_path, 'daily', str(target))
    assert rebound.quality == 'PROVISIONAL_PUBLIC' and rebound.events == []
    assert hashlib.sha256(mp.read_bytes()).digest() == hashlib.sha256(original_markdown).digest()


def test_history_source_changes_after_projection_before_acceptance(tmp_path, monkeypatch):
    target, _, _ = _bound_zero_report(tmp_path)
    source = tmp_path/'data/2026/daily/2026-10-17.json'
    original_bytes = source.read_bytes()
    original_hash = hashlib.sha256(original_bytes).hexdigest()
    actual_loader = promotion_history.load_promotion_history
    projected_hashes = []

    def mutate_actual_source_after_projection(*args, **kwargs):
        rows, history = actual_loader(*args, **kwargs)
        gap = next(item for item in history['unusable'] if item['date'] == '2026-10-17')
        projected_hashes.append(gap['source_receipt']['sha256'])
        # Valid JSON whitespace changes actual bytes after the real bounded reader
        # has closed its pair. Do not alter rows, saved metadata or any receipt.
        with source.open('ab') as stream:
            stream.write(b' ')
        assert json.loads(source.read_bytes()) == json.loads(original_bytes)
        assert hashlib.sha256(source.read_bytes()).hexdigest() != original_hash
        return rows, history

    monkeypatch.setattr(promotion_history, 'load_promotion_history', mutate_actual_source_after_projection)
    with pytest.raises(GateError) as failure:
        verify(tmp_path, 'daily', str(target))
    assert failure.value.code == 'HISTORY_INDEX_SOURCE_MISMATCH'
    assert projected_hashes == [original_hash]
