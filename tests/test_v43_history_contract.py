"""Saved incident regression: originals remain read-only; adversarial changes are isolated."""
from datetime import date, timedelta
from pathlib import Path
import hashlib
import json
import os
import shutil
import pytest
from lattice_digest.history_resources import load_verified_history_pair, HistoryEvidenceError
from lattice_digest.promotion_history import load_promotion_history
from lattice_digest.report_gate import verify, GateError

ROOT = Path(os.environ.get('V41_ORIGINAL_ROOT', r'D:/Code/CodexProjects/lattice-crypto-daily-digest'))

def original(day):
    p = ROOT / f'data/2026/daily/{day}.json'
    if not p.exists(): pytest.skip('private saved incident input unavailable')
    return p

def test_oct17_is_bound_missing_observation_placeholder(tmp_path):
    fixture = Path(__file__).parent/'fixtures/v43_oct17'
    for kind, ext in [('data','json'), ('digests','md')]:
        out=tmp_path/f'{kind}/2026/daily/2026-10-17.{ext}'
        out.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(fixture/f'2026-10-17.{ext}',out)
    p=tmp_path/'data/2026/daily/2026-10-17.json'
    assert hashlib.sha256(p.read_bytes()).hexdigest() == 'b07e74b6fdf438b6d9bafbc9c49b978e222d8b4ed6f49742179b345376cde874'
    with pytest.raises(HistoryEvidenceError) as failure:
        load_verified_history_pair(tmp_path/'data', date(2026,10,17))
    exc=failure.value
    assert exc.code == 'HISTORY_ORIGINAL_OBSERVATIONS_UNKNOWN'
    assert exc.receipt['source_pair_binding']=='SOURCE_PAIR_VALID'
    assert exc.receipt['history_trust_tier']=='UNVERIFIED_OR_MISSING'
    assert not exc.receipt['positive_event_ownership']
    assert not exc.rows

@pytest.mark.parametrize('day,size', [('2026-10-26',33998116),('2026-10-30',34790320)])
def test_large_real_pair_qa_never_claims_independent_acceptance(day,size):
    assert original(day).stat().st_size == size
    rows, receipt=load_verified_history_pair(ROOT/'data',date.fromisoformat(day))
    assert rows and receipt['source_bytes']==size
    assert receipt['independent_report_acceptance']=='UNKNOWN'
    assert receipt['positive_event_ownership'] is False
    assert all(r['_history_positive_event_owner'] is False for r in rows)

def test_oct30_original_requires_source_bound_revalidation():
    original('2026-10-30')
    # Original rejected metadata lacks the Oct17 source hash. It cannot be
    # retrospectively accepted in place; a source-preserving derived pair is
    # independently checked in the binding regression and actual recovery E2E.
    with pytest.raises(GateError) as failure:
        verify(ROOT,'daily','2026-10-30')
    assert failure.value.code == 'HISTORY_PROJECTION_UNBOUND'


def test_legacy_shape_requires_pair_binding_before_durable_qa(tmp_path):
    p=original('2026-10-30'); payload=json.loads(p.read_bytes())
    for k in ('publication_state','structural_qa'): payload['metadata'].pop(k,None)
    j=tmp_path/'data/2026/daily/2026-10-30.json';j.parent.mkdir(parents=True)
    m=tmp_path/'digests/2026/daily/2026-10-30.md';m.parent.mkdir(parents=True)
    j.write_text(json.dumps(payload),'utf-8');shutil.copyfile(ROOT/'digests/2026/daily/2026-10-30.md',m)
    with pytest.raises(HistoryEvidenceError) as f:load_verified_history_pair(tmp_path/'data',date(2026,10,30))
    assert f.value.code=='HISTORY_ORIGINAL_QA_UNCONFIRMED'
    assert f.value.receipt['history_trust_tier']=='LEGACY_INTEGRITY_VERIFIED'
    m.write_bytes(m.read_bytes()+b'corrupt')
    with pytest.raises(HistoryEvidenceError) as f:load_verified_history_pair(tmp_path/'data',date(2026,10,30))
    assert f.value.code=='HISTORY_INDEX_SOURCE_MISMATCH'

def test_sixteen_date_rolling_gap_never_becomes_positive_authority(tmp_path):
    # Controlled simulation, explicitly not an original execution claim. Use
    # the actual placeholder bytes for the initial gap and real incident row.
    from lattice_digest.publication_events import build_event_ledger
    from tests.v41_history_fixture import seed_empty_history
    payload=json.loads(original('2026-10-30').read_bytes())
    row=next(r for r in payload['records'] if r.get('doi')=='10.21203/rs.3.rs-11270790/v1') if any(r.get('doi')=='10.21203/rs.3.rs-11270790/v1' for r in payload['records']) else payload['records'][0]
    start=date(2026,10,18)
    seed_empty_history(tmp_path,start)
    for kind,ext in [('data','json'),('digests','md')]:
        shutil.copyfile(ROOT/f'{kind}/2026/daily/2026-10-17.{ext}',tmp_path/f'{kind}/2026/daily/2026-10-17.{ext}')
    for offset in range(16):
        target=start+timedelta(days=offset)
        prior,evidence=load_promotion_history(tmp_path/'data',target)
        assert evidence['complete'] is (target>date(2026,10,31))
        meta={**payload['metadata'],'target_date':str(target),'coverage_start':str(target)+'T00:00:00+00:00','coverage_end':str(target+timedelta(days=1))+'T00:00:00+00:00','promotion_history':evidence}
        ledger=build_event_ledger([row],meta,prior)
        assert ledger['counts']['primary_new']==0
        seed_empty_history(tmp_path,target+timedelta(days=1),days=1)
