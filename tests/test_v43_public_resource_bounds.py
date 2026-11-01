"""Linked period inputs and delivery state cannot escape bounded readers."""
from datetime import date
import json
from pathlib import Path
import pytest
from lattice_digest.public_delivery import pending
from lattice_digest.monthly_synthesis import _weekly_files_for_month
from lattice_digest.report_gate import GateError


def test_pending_receipt_does_not_use_unbounded_second_read(tmp_path, monkeypatch):
    path = tmp_path/'audits/public-delivery/daily/2026-10-30/receipt.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(dict(report_type='daily',report_period='2026-10-30',status='PUBLISH_PENDING')))
    monkeypatch.setattr(Path, 'read_bytes', lambda p:pytest.fail('pending state reached unbounded read'))
    assert pending(tmp_path, 'daily') == ['2026-10-30']


def test_oversized_pending_receipt_cannot_authorize_retry(tmp_path):
    path = tmp_path/'audits/public-delivery/daily/2026-10-30/receipt.json'
    path.parent.mkdir(parents=True)
    with path.open('wb') as stream:stream.truncate(16385)
    with pytest.raises(GateError, match='PAYLOAD_SIZE_INVALID'):pending(tmp_path, 'daily')


def test_pending_nonmapping_is_a_controlled_rejection(tmp_path):
    path = tmp_path/'audits/public-delivery/daily/2026-10-30/receipt.json'
    path.parent.mkdir(parents=True);path.write_text('[]')
    with pytest.raises(GateError, match='SCHEMA_INVALID'):pending(tmp_path, 'daily')


def test_monthly_linked_weekly_input_is_bounded_before_decode(tmp_path, monkeypatch):
    import lattice_digest.report_gate as gate
    path = tmp_path/'data/2026/weekly/2026-W44.json'
    path.parent.mkdir(parents=True)
    with path.open('wb') as stream:stream.truncate(64*1024*1024+1)
    monkeypatch.setattr(gate, 'strict_json', lambda b:pytest.fail('oversized reference reached decoder'))
    with pytest.raises(GateError, match='PAYLOAD_SIZE_INVALID'):
        _weekly_files_for_month(tmp_path/'data',date(2026,10,1),date(2026,10,31))
