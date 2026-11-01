"""Final source snapshot recheck against byte-exact Oct17 incident fixtures."""
from copy import deepcopy
from datetime import date
import hashlib
import os
from pathlib import Path
import shutil
import pytest
from lattice_digest import history_resources as resources
from lattice_digest.promotion_history import load_promotion_history

FIXTURE=Path(__file__).parent/'fixtures/v43_oct17'
DAY=date(2026,10,17)

@pytest.fixture
def projected(tmp_path):
    for kind,extension in [('data','json'),('digests','md')]:
        path=tmp_path/kind/'2026/daily'/f'{DAY}.{extension}'
        path.parent.mkdir(parents=True)
        shutil.copyfile(FIXTURE/f'{DAY}.{extension}',path)
    assert hashlib.sha256((tmp_path/'data/2026/daily/2026-10-17.json').read_bytes()).hexdigest()=='b07e74b6fdf438b6d9bafbc9c49b978e222d8b4ed6f49742179b345376cde874'
    rows,evidence=load_promotion_history(tmp_path/'data',date(2026,10,18),days=1)
    assert not rows
    assert evidence['unusable'][0]['code']=='HISTORY_ORIGINAL_OBSERVATIONS_UNKNOWN'
    return tmp_path,evidence


def reject(root,evidence):
    with pytest.raises(resources.HistoryEvidenceError) as failure:
        resources.verify_history_source_bindings(root/'data',evidence)
    assert failure.value.code=='HISTORY_INDEX_SOURCE_MISMATCH'


def test_actual_legacy_fixture_rechecks_without_claiming_original_qa(projected):
    root,evidence=projected
    resources.verify_history_source_bindings(root/'data',evidence)
    assert evidence['unusable'][0]['source_receipt']['durable_qa_state']=='NOT_ORIGINAL_EXECUTION'


@pytest.mark.parametrize('extension,kind',[('json','data'),('md','digests')])
def test_real_source_changed_after_projection_rejected_even_restored_mtime(projected,extension,kind):
    root,evidence=projected
    path=root/kind/'2026/daily'/f'{DAY}.{extension}'
    before=path.stat();raw=bytearray(path.read_bytes());raw[-1] = 32 if raw[-1]!=32 else 10
    path.write_bytes(raw)
    os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns))
    reject(root,evidence)


@pytest.mark.parametrize('mutation',['json_hash','md_hash','date','source_size','empty','omitted_day'])
def test_fake_reader_receipts_do_not_replace_source_readback(projected,mutation):
    root,evidence=projected;evidence=deepcopy(evidence)
    receipt=evidence['unusable'][0]['source_receipt']
    if mutation=='json_hash':receipt['sha256']='0'*64
    if mutation=='md_hash':receipt['markdown_sha256']='0'*64
    if mutation=='date':receipt['date']='2026-10-16'
    if mutation=='source_size':receipt['source_bytes']+=1
    if mutation=='empty':evidence['unusable'][0]['source_receipt']={}
    if mutation=='omitted_day':evidence['unusable']=[]
    reject(root,evidence)


def test_missing_day_appearing_after_projection_is_not_silently_accepted(tmp_path):
    _,evidence=load_promotion_history(tmp_path/'data',date(2026,10,18),days=1)
    resources.verify_history_source_bindings(tmp_path/'data',evidence)
    path=tmp_path/'data/2026/daily/2026-10-17.json';path.parent.mkdir(parents=True)
    shutil.copyfile(FIXTURE/'2026-10-17.json',path)
    reject(tmp_path,evidence)


@pytest.mark.parametrize('publication_lock',[False,True])
def test_new_writer_lock_after_projection_rejected(projected,publication_lock):
    root,evidence=projected
    path=(root/'data/2026/daily/.2026-10-17.publication.lock' if publication_lock
          else root/'audits/writer-locks/DAILY-2026-10-17.lock')
    path.parent.mkdir(parents=True,exist_ok=True);path.touch()
    reject(root,evidence)


def test_growth_during_streaming_recheck_rejected(projected,monkeypatch):
    root,evidence=projected
    original=resources._safe_open
    changed=[]
    class ChangingStream:
        def __init__(self,stream,path):self.stream=stream;self.path=path
        def __enter__(self):return self
        def __exit__(self,*args):self.stream.close()
        def fileno(self):return self.stream.fileno()
        def read(self,size):
            chunk=self.stream.read(size)
            if chunk and not changed:
                changed.append(True)
                with self.path.open('ab') as output:output.write(b' ')
            return chunk
    def opened(path,maximum):
        stream,before=original(path,maximum)
        return ChangingStream(stream,path),before
    monkeypatch.setattr(resources,'_safe_open',opened)
    reject(root,evidence)


def test_resource_growth_after_projection_fails_without_allocating_archive(projected):
    root,evidence=projected
    path=root/'data/2026/daily/2026-10-17.json'
    with path.open('r+b') as stream:stream.truncate(resources.MAX_HISTORY_BYTES+1)
    reject(root,evidence)
