"""Period delivery unit regressions; public-entry historical E2E is separate."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from lattice_digest import period_delivery as delivery
from lattice_digest import public_daily, public_weekly, public_monthly


def paths(root):
    return SimpleNamespace(audit_root=root/'audits', data_root=root/'data',
        digest_root=root/'digests', canonical_root=root, as_dict=lambda: {'canonical_root': str(root)})


def candidate():
    return {'coverage': {'authority_state': 'AUTHORITATIVE_DEGRADED'},
            'publication_event_views': {'events': []}, 'metadata': {}}


def writer(payload, data, digests):
    j=data/'2026/weekly/2026-W42.json';m=digests/'2026/weekly/2026-W42.md'
    j.parent.mkdir(parents=True);m.parent.mkdir(parents=True)
    j.write_text(json.dumps(payload),encoding='utf-8')
    m.write_text('# Weekly 2026-W42\n\n来源覆盖降级。\n',encoding='utf-8')
    return j,m


@pytest.mark.parametrize('profile,key',[('DAILY','2026-10-19'),('WEEKLY','2026-W42'),('MONTHLY','2026-09')])
def test_single_writer_prevents_same_period_and_preserves_owner_lock(tmp_path,profile,key):
    p=paths(tmp_path)
    with delivery.writer_lock(p,profile,key):
        lock=p.audit_root/'writer-locks'/f'{profile}-{key}.lock'
        original=lock.read_bytes()
        with pytest.raises(ValueError,match='ACTIVE_OR_STALE_WRITER_LOCK'):
            with delivery.writer_lock(p,profile,key):
                pytest.fail('second writer entered')
        assert lock.read_bytes()==original
    assert not lock.exists()


def test_writer_lock_releases_after_pipeline_failure(tmp_path):
    p=paths(tmp_path)
    with pytest.raises(OSError):
        with delivery.writer_lock(p,'DAILY','2026-10-19'):
            raise OSError('simulated generation failure')
    with delivery.writer_lock(p,'DAILY','2026-10-19'):
        pass


def test_complete_pair_generation_and_markdown_integrity(tmp_path):
    p=paths(tmp_path);original=candidate();snapshot=deepcopy(original)
    j,m=delivery.publish_period(original,p,writer)
    assert delivery.verify_period_pair(j,m)['status']=='PASS'
    assert original==snapshot
    materialized=json.loads(j.read_text('utf-8'))
    assert materialized['metadata']['markdown_sha256']==hashlib.sha256(m.read_bytes()).hexdigest()
    assert '<!-- generation:'+materialized['metadata']['generation_id']+' -->' in m.read_text('utf-8')
    assert not list(tmp_path.rglob('.staged-*'))


@pytest.mark.parametrize('existing',['json','markdown','both'])
def test_existing_pair_and_orphan_never_overwritten(tmp_path,existing):
    p=paths(tmp_path);j=p.data_root/'2026/weekly/2026-W42.json';m=p.digest_root/'2026/weekly/2026-W42.md'
    before={}
    for kind,target in [('json',j),('markdown',m)]:
        if existing in (kind,'both'):
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(b'ORIGINAL EVIDENCE')
            before[target]=target.read_bytes()
    with pytest.raises(ValueError,match='existing period pair/orphan'):
        delivery.publish_period(candidate(),p,writer)
    assert all(target.read_bytes()==content for target,content in before.items())
    assert j.exists()==(existing in ('json','both'))
    assert m.exists()==(existing in ('markdown','both'))


def test_link_failure_between_markdown_and_json_rolls_back_only_new_files(tmp_path,monkeypatch):
    p=paths(tmp_path);link=delivery.os.link;calls=[]
    def fail_second(source,target):
        calls.append(target)
        if len(calls)==2:
            raise OSError('injected second-link failure')
        return link(source,target)
    monkeypatch.setattr(delivery.os,'link',fail_second)
    with pytest.raises(OSError,match='second-link'):
        delivery.publish_period(candidate(),p,writer)
    assert not list(p.data_root.rglob('*.json'))
    assert not list(p.digest_root.rglob('*.md'))
    assert not list(tmp_path.rglob('.staged-*'))


def test_staged_write_failure_does_not_leave_partial_staged_or_canonical_files(tmp_path,monkeypatch):
    p=paths(tmp_path);factory=delivery.tempfile.NamedTemporaryFile
    class BrokenWrite:
        def __init__(self,stream):self.stream=stream;self.name=stream.name
        def __enter__(self):self.stream.__enter__();return self
        def __exit__(self,*args):return self.stream.__exit__(*args)
        def write(self,content):
            self.stream.write(content[:3]);raise OSError('injected staged write failure')
    monkeypatch.setattr(delivery.tempfile,'NamedTemporaryFile',lambda *a,**kw:BrokenWrite(factory(*a,**kw)))
    with pytest.raises(OSError,match='staged write'):
        delivery.publish_period(candidate(),p,writer)
    assert not list(p.data_root.rglob('*.json'))
    assert not list(p.digest_root.rglob('*.md'))
    assert not list(tmp_path.rglob('.staged-*'))


def test_markdown_tamper_and_generation_mismatch_rejected(tmp_path):
    j,m=delivery.publish_period(candidate(),paths(tmp_path),writer)
    original=m.read_bytes();m.write_bytes(original+b'altered')
    with pytest.raises(ValueError,match='hash mismatch'):
        delivery.verify_period_pair(j,m)
    m.write_bytes(original.replace(b'generation:',b'forged:'))
    with pytest.raises(ValueError,match='generation mismatch'):
        delivery.verify_period_pair(j,m)


def test_markdown_byte_hash_detects_windows_newline_tamper(tmp_path):
    j,m=delivery.publish_period(candidate(),paths(tmp_path),writer)
    m.write_bytes(m.read_bytes().replace(b'\n',b'\r\n'))
    with pytest.raises(ValueError,match='hash mismatch'):
        delivery.verify_period_pair(j,m)


def test_machine_event_metadata_tamper_cannot_reuse_pair_verification(tmp_path):
    j,m=delivery.publish_period(candidate(),paths(tmp_path),writer)
    data=json.loads(j.read_text('utf-8'))
    data['publication_event_views']['events']=[{'event_id':'FORGED','count':999}]
    j.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(ValueError):
        delivery.verify_period_pair(j,m)


def test_failed_daily_inputs_cannot_claim_complete_period(tmp_path):
    p=candidate();p['coverage'].update(authority_state='AUTHORITATIVE_COMPLETE',semantic_failed_days=['2026-10-17'])
    with pytest.raises(ValueError,match='input_failure_authority_upgrade'):
        delivery.publish_period(p,paths(tmp_path),writer)
    assert not list(tmp_path.rglob('*.json')) and not list(tmp_path.rglob('*.md'))


class Frozen(datetime):
    @classmethod
    def now(cls,tz=None):return cls(2026,10,19,10,35,tzinfo=tz)


@pytest.mark.parametrize('start,end,expected',[
    ('2026-10-12','2026-10-18',0),('2026-10-05','2026-10-11',0),
    ('2026-10-19','2026-10-25',2),('2026-10-12','2026-10-17',2),
    ('2026-10-13','2026-10-19',2)])
def test_weekly_public_preflight_requires_complete_iso_week(tmp_path,monkeypatch,start,end,expected):
    monkeypatch.setattr(public_weekly,'datetime',Frozen)
    monkeypatch.setattr(public_weekly,'public_preflight',lambda _: (paths(tmp_path),{}))
    monkeypatch.setattr(public_weekly,'record_entry_failure',lambda *a,**kw:None)
    assert public_weekly.main(['--preflight','--from-date',start,'--to-date',end])==expected
    assert not list(tmp_path.rglob('*.json'))


@pytest.mark.parametrize('month,expected',[('2026-09',0),('2026-10',2),('2026-11',2),('2025-12',0)])
def test_monthly_public_preflight_requires_completed_calendar_month(tmp_path,monkeypatch,month,expected):
    monkeypatch.setattr(public_monthly,'datetime',Frozen)
    monkeypatch.setattr(public_monthly,'public_preflight',lambda _: (paths(tmp_path),{}))
    monkeypatch.setattr(public_monthly,'record_entry_failure',lambda *a,**kw:None)
    assert public_monthly.main(['--preflight','--month',month])==expected
    assert not list(tmp_path.rglob('*.json'))


@pytest.mark.parametrize('arguments,expected',[
    (['--target-date','2026-10-15'],'2026-10-15'),
    (['--date','2026-10-16'],'2026-10-16'),([], '2026-10-19')])
def test_daily_lock_key_accepts_real_string_date_and_default_types(tmp_path,monkeypatch,arguments,expected):
    captured=[]
    @contextmanager
    def lock(paths,profile,key):captured.append((profile,key));yield
    monkeypatch.setattr(public_daily,'datetime',Frozen)
    monkeypatch.setattr(public_daily,'public_preflight',lambda _: (paths(tmp_path),{}))
    monkeypatch.setattr(public_daily,'doctor_report',lambda **kw:(0,{}))
    monkeypatch.setattr(public_daily,'writer_lock',lock)
    monkeypatch.setattr(public_daily.run,'main',lambda *a,**kw:0)
    monkeypatch.setenv('LATTICE_DIGEST_PUBLIC_AUTOMATION','0')
    assert public_daily.main(arguments)==0
    assert captured==[('DAILY',expected)]
