"""Acceptance-state regressions; no credentials, network, or Git mutations."""
from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from lattice_digest import delivery_receipt as receipts
from lattice_digest import public_daily, public_delivery
from lattice_digest.report_gate import GateError


@pytest.mark.parametrize('code,status', [
    ('HISTORY_RESOURCE_LIMIT', receipts.HISTORY_EVIDENCE_BLOCKED),
    ('HISTORY_EVIDENCE_UNUSABLE', receipts.HISTORY_EVIDENCE_BLOCKED),
    ('HISTORY_INDEX_SOURCE_MISMATCH', receipts.HISTORY_EVIDENCE_BLOCKED),
    ('CROSS_DAY_DUPLICATE_PRIMARY', receipts.SCIENTIFIC_VALIDATION_FAILED),
    ('SCIENTIFIC_QA_INCOMPLETE', receipts.SCIENTIFIC_VALIDATION_FAILED),
])
def test_generated_pair_is_never_delivery_when_independent_gate_rejects(tmp_path, monkeypatch, code, status):
    original=tmp_path/'data/2026/daily/2026-10-27.json'
    original.parent.mkdir(parents=True)
    original.write_bytes(b'preserved-original-canonical-canary')
    def reject(*args):
        raise GateError(code, 'private-source-path-and-row-canary')
    monkeypatch.setattr(receipts, 'verify', reject)
    receipt=receipts.validate_generated(tmp_path, 'daily', '2026-10-27')
    assert receipt['status']==status
    assert not receipt['scientific_validation_verified']
    assert not any(receipt[k] for k in ('delivery_verified','publication_verified','publish_pending'))
    assert 'private-source-path-and-row-canary' not in json.dumps(receipt)
    saved=json.loads((tmp_path/'audits/generation-validation/daily/2026-10-27/receipt.json').read_bytes())
    assert saved==receipt
    assert original.read_bytes()==b'preserved-original-canonical-canary'


def test_validated_pair_receipt_does_not_claim_publication(tmp_path,monkeypatch):
    pair=SimpleNamespace(payload={'metadata':{'generation_id':'a'*32}},
                         json_sha256='b'*64,markdown_sha256='c'*64)
    monkeypatch.setattr(receipts,'verify',lambda *args:pair)
    receipt=receipts.validate_generated(tmp_path,'daily','2026-10-27')
    assert receipt['status']==receipts.CANONICAL_VALIDATED
    assert receipt['scientific_validation_verified'] is True
    assert receipt['publication_verified'] is receipt['delivery_verified'] is receipt['publish_pending'] is False


def test_public_daily_gate_runs_after_writer_release_and_propagates_failure(tmp_path,monkeypatch,capsys):
    active=[]
    @contextmanager
    def lock(*args):
        active.append(True)
        try:yield
        finally:active.pop()
    monkeypatch.setattr(public_daily,'public_preflight',lambda _: (SimpleNamespace(canonical_root=tmp_path),{}))
    monkeypatch.setattr(public_daily,'doctor_report',lambda **kwargs:(0,{}))
    monkeypatch.setattr(public_daily,'writer_lock',lock)
    monkeypatch.setattr(public_daily.run,'main',lambda *args,**kwargs:0)
    def independent(*args):
        assert not active
        return {'status':receipts.HISTORY_EVIDENCE_BLOCKED,'error_code':'HISTORY_EVIDENCE_UNUSABLE',
                'scientific_validation_verified':False}
    monkeypatch.setattr(public_daily,'validate_generated',independent)
    assert public_daily.main(['--target-date','2026-10-27'])==2
    assert 'HISTORY_EVIDENCE_BLOCKED' in capsys.readouterr().out


def delivery_fixture(monkeypatch):
    pair=SimpleNamespace(payload={'metadata':{'generation_id':'a'*32}})
    monkeypatch.setattr(public_delivery,'verify',lambda *args:pair)
    monkeypatch.setattr(public_delivery,'project',lambda _: {
        'public_generation_id':'b'*64,'canonical_pair_sha256':{'json':'c'*64,'markdown':'d'*64}})
    monkeypatch.setattr(public_delivery,'export',lambda *args:args[-1].mkdir())
    monkeypatch.setattr(public_delivery,'inspect_tree',lambda *args:({},{}))


@pytest.mark.parametrize('code',['EVENT_OWNERSHIP_CONFLICT','EVENT_OWNERSHIP_INVALID','CROSS_DAY_DUPLICATE_PRIMARY'])
def test_ownership_rejection_is_blocked_not_pending(tmp_path,monkeypatch,code):
    delivery_fixture(monkeypatch)
    def reject(*args,**kwargs):raise GateError(code,'private-row-canary')
    monkeypatch.setattr(public_delivery,'publish',reject)
    receipt=public_delivery.deliver(tmp_path,'daily','2026-10-27',approved=True)
    assert receipt['status']==receipts.REMOTE_PUBLICATION_BLOCKED
    assert receipt['delivery_status']==receipts.REMOTE_PUBLICATION_BLOCKED
    assert receipt['publish_pending'] is receipt['delivery_verified'] is False
    assert public_delivery.pending(tmp_path,'daily')==[]
    assert 'private-row-canary' not in json.dumps(receipt)


def test_failed_scientific_gate_is_durable_and_cannot_enter_export(tmp_path,monkeypatch):
    def reject(*args):raise GateError('HISTORY_RESOURCE_LIMIT','private-path-canary')
    def forbidden(*args,**kwargs):raise AssertionError('export/publish must not run')
    monkeypatch.setattr(public_delivery,'verify',reject)
    monkeypatch.setattr(public_delivery,'project',forbidden)
    monkeypatch.setattr(public_delivery,'publish',forbidden)
    receipt=public_delivery.deliver(tmp_path,'daily','2026-10-27',approved=True)
    assert receipt['status']==receipts.HISTORY_EVIDENCE_BLOCKED
    assert receipt['states']==[]
    assert not receipt['publish_pending']
    saved=json.loads((tmp_path/'audits/public-delivery/daily/2026-10-27/receipt.json').read_bytes())
    assert saved==receipt


def test_timeout_remains_retry_compatible_only_after_verified_export(tmp_path,monkeypatch):
    delivery_fixture(monkeypatch)
    def timeout(*args,**kwargs):raise subprocess.TimeoutExpired('private-command-canary',60)
    monkeypatch.setattr(public_delivery,'publish',timeout)
    receipt=public_delivery.deliver(tmp_path,'daily','2026-10-27',approved=True)
    assert receipt['status']=='PUBLISH_PENDING'
    assert receipt['delivery_status']==receipts.REMOTE_PUBLICATION_BLOCKED
    assert receipt['publish_pending'] is True
    assert receipt['delivery_verified'] is False
    assert public_delivery.pending(tmp_path,'daily')==['2026-10-27']
    assert 'private-command-canary' not in json.dumps(receipt)


def test_export_privacy_failure_is_ineligible(tmp_path,monkeypatch):
    delivery_fixture(monkeypatch)
    def reject(*args):raise GateError('PUBLIC_PRIVACY_GATE_FAILED','private-note-canary')
    monkeypatch.setattr(public_delivery,'project',reject)
    receipt=public_delivery.deliver(tmp_path,'daily','2026-10-27',approved=True)
    assert receipt['status']==receipts.PUBLIC_EXPORT_INELIGIBLE
    assert not receipt['publish_pending']
    assert 'private-note-canary' not in json.dumps(receipt)
