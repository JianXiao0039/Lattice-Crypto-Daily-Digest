"""Post-generation acceptance receipts; canonical creation is not delivery.

Receipts contain fixed diagnostics and hashes only, never canonical rows or paths.
They are deliberately separate from the immutable scientific source pair.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile

from lattice_digest.public_contract import _reject_redirects
from lattice_digest.report_gate import GateError, encoded, period_bounds, verify


CANONICAL_CREATED_VALIDATION_PENDING = 'CANONICAL_CREATED_VALIDATION_PENDING'
SCIENTIFIC_VALIDATION_FAILED = 'SCIENTIFIC_VALIDATION_FAILED'
HISTORY_EVIDENCE_BLOCKED = 'HISTORY_EVIDENCE_BLOCKED'
PUBLIC_EXPORT_INELIGIBLE = 'PUBLIC_EXPORT_INELIGIBLE'
REMOTE_PUBLICATION_BLOCKED = 'REMOTE_PUBLICATION_BLOCKED'
DELIVERY_VERIFIED = 'DELIVERY_VERIFIED'
CANONICAL_VALIDATED = 'CANONICAL_VALIDATED_PUBLICATION_NOT_ATTEMPTED'

HISTORY_ERRORS = frozenset({
    'HISTORY_EVIDENCE_UNUSABLE', 'HISTORY_INDEX_SOURCE_MISMATCH',
    'HISTORY_RESOURCE_LIMIT', 'HISTORY_EVIDENCE_INCOMPLETE',
})


def failure_state(code: str, *, stage: str = 'SCIENTIFIC') -> str:
    if code in HISTORY_ERRORS:
        return HISTORY_EVIDENCE_BLOCKED
    if stage == 'REMOTE':
        return REMOTE_PUBLICATION_BLOCKED
    if stage == 'EXPORT':
        return PUBLIC_EXPORT_INELIGIBLE
    return SCIENTIFIC_VALIDATION_FAILED


def save_receipt(root: Path, kind: str, period: str, receipt: dict) -> None:
    """Atomic bounded receipt materialization without changing the canonical pair."""
    period_bounds(kind, period)
    directory = Path(root) / 'audits' / 'generation-validation' / kind / period
    _reject_redirects(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'receipt.json'
    _reject_redirects(target)
    content = encoded(receipt) + b'\n'
    if len(content) > 16 * 1024:
        raise ValueError('delivery validation receipt exceeds fixed budget')
    staged = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, prefix='.receipt-', delete=False) as stream:
            staged = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        _reject_redirects(target)
        os.replace(staged, target)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def write_generation_receipt(root: Path, kind: str, period: str) -> dict:
    receipt = {
        'schema_version': 'generation-validation-v41',
        'report_type': kind, 'report_period': period,
        'status': CANONICAL_CREATED_VALIDATION_PENDING,
        'states': [CANONICAL_CREATED_VALIDATION_PENDING],
        'created_at': datetime.now(timezone.utc).isoformat(),
        'scientific_validation_verified': False,
        'public_export_verified': False, 'publication_verified': False,
        'remote_readback_verified': False, 'publish_pending': False,
        'delivery_verified': False,
    }
    save_receipt(root, kind, period, receipt)
    return receipt


def validate_generated(root: Path, kind: str, period: str) -> dict:
    """Independently check a completed pair after its generation lock is released."""
    receipt = write_generation_receipt(root, kind, period)
    try:
        pair = verify(root, kind, period)
    except (GateError, OSError, ValueError, KeyError, TypeError) as exc:
        code = exc.code if isinstance(exc, GateError) else 'SCIENTIFIC_QA_INCOMPLETE'
        receipt.update(status=failure_state(code), error_code=code)
    else:
        receipt.update(status=CANONICAL_VALIDATED, scientific_validation_verified=True,
                       source_generation_id=pair.payload['metadata']['generation_id'],
                       canonical_pair_sha256={'json': pair.json_sha256,
                                              'markdown': pair.markdown_sha256})
    receipt['states'].append(receipt['status'])
    receipt['finished_at'] = datetime.now(timezone.utc).isoformat()
    save_receipt(root, kind, period, receipt)
    return receipt
