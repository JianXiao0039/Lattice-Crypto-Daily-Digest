"""Period inputs receive the same bounded path checks as independent gates."""
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from lattice_digest.daily_inputs import assess_daily_input, summarize_daily_inputs, PERIOD_INPUT_POLICY_V43

DAY = date(2026, 10, 30)


def pair(root, payload=None, markdown=b'# Source-bound input\r\n\r\nObservation only.\r\n'):
    j = root/'data/2026/daily/2026-10-30.json'
    m = root/'digests/2026/daily/2026-10-30.md'
    j.parent.mkdir(parents=True, exist_ok=True); m.parent.mkdir(parents=True, exist_ok=True)
    j.write_text(json.dumps(payload if payload is not None else {'metadata':{}, 'records':[]}), encoding='utf-8')
    m.write_bytes(markdown)
    return j,m


def assess(root, path):
    return assess_daily_input(path, DAY, root/'data', assessment_policy=PERIOD_INPUT_POLICY_V43)


def assert_unavailable(root, path, defect):
    result = assess(root,path); q=result['_daily_input_quality']
    assert not q['semantic_valid'] and not q['fully_valid']
    assert defect in q['defects']
    assert summarize_daily_inputs([(DAY,result)],[])['authority_state'] == 'INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'
    return q


def test_json_cap_rejected_before_decoder(tmp_path, monkeypatch):
    from lattice_digest import report_gate
    j,_=pair(tmp_path)
    with j.open('wb') as f:f.truncate(64*1024*1024+1)
    monkeypatch.setattr(report_gate,'strict_json',lambda raw:pytest.fail('oversized source reached JSON decoder'))
    q=assert_unavailable(tmp_path,j,'PERIOD_INPUT_JSON_UNAVAILABLE')
    assert not q['structural_valid']


def test_markdown_cap_does_not_read_as_valid_empty_day(tmp_path):
    j,m=pair(tmp_path)
    with m.open('wb') as f:f.truncate(16*1024*1024+1)
    assert_unavailable(tmp_path,j,'PERIOD_INPUT_MARKDOWN_UNAVAILABLE')


@pytest.mark.parametrize('payload',[[], {'metadata':{},'records':[]}])
def test_legacy_list_and_mapping_preserved_and_crlf_not_normalized(tmp_path, monkeypatch, payload):
    import lattice_digest.daily_inputs as reader
    j,m=pair(tmp_path,payload); captured=[]; real=reader.semantic_qa
    def qa(p,text,**kwargs):
        captured.append(text);return real(p,text,**kwargs)
    monkeypatch.setattr(reader,'semantic_qa',qa)
    result=assess(tmp_path,j)
    assert result['records'] == [] and result['_daily_input_quality']['structural_valid']
    assert captured[0].encode('utf-8') == m.read_bytes()


def test_path_escape_is_rejected_without_decoding(tmp_path,monkeypatch):
    from lattice_digest import report_gate
    root=tmp_path/'selected'; j,_=pair(root)
    external=tmp_path/'external.json';external.write_text('{"records":[]}',encoding='utf-8')
    monkeypatch.setattr(report_gate,'strict_json',lambda raw:pytest.fail('escaped source reached decoder'))
    assert_unavailable(root,external,'PERIOD_INPUT_JSON_UNAVAILABLE')
    lexical=j.parent/'../../../../external.json'
    assert_unavailable(root,lexical,'PERIOD_INPUT_JSON_UNAVAILABLE')


@pytest.mark.parametrize('kind',['json','markdown'])
def test_source_symlink_rejected(tmp_path,kind):
    j,m=pair(tmp_path); selected=j if kind=='json' else m
    target=tmp_path/('original-'+selected.name);selected.rename(target)
    try:selected.symlink_to(target)
    except (OSError,NotImplementedError):pytest.skip('symlink creation unavailable')
    try:assert_unavailable(tmp_path,j,'PERIOD_INPUT_JSON_UNAVAILABLE' if kind=='json' else 'PERIOD_INPUT_MARKDOWN_UNAVAILABLE')
    finally:selected.unlink()


@pytest.mark.skipif(os.name!='nt',reason='NTFS junction contract')
def test_junction_directory_rejected(tmp_path):
    real=tmp_path/'real';j,_=pair(real); root=tmp_path/'selected'; root.mkdir()
    link=root/'data'
    completed=subprocess.run(['cmd','/c','mklink','/J',str(link),str(real/'data')],capture_output=True)
    if completed.returncode:pytest.skip('junction creation unavailable')
    try:assert_unavailable(root,link/'2026/daily/2026-10-30.json','PERIOD_INPUT_JSON_UNAVAILABLE')
    finally:os.rmdir(link)  # Remove only the junction, never its target tree.


@pytest.mark.parametrize('day,size,digest',[
    ('2026-10-26',33998116,'57ce85cb8cc85b0a5ea9fe75d0b65b34f11a988914e210f5d33b5c30317647e5'),
    ('2026-10-30',34790320,'089b64fd52f953ea7f73fe2a69bba86a5e7cb30f19aa3c5c8c4c59d7edc36778')])
def test_actual_large_canonical_is_within_bounded_period_contract(day,size,digest):
    root=Path('D:/Code/CodexProjects/lattice-crypto-daily-digest')
    path=root/'data/2026/daily'/f'{day}.json'
    if not path.is_file():pytest.skip('actual private canonical corpus unavailable; portable shape tests run separately')
    assert path.stat().st_size==size and hashlib.sha256(path.read_bytes()).hexdigest()==digest
    result=assess_daily_input(path,date.fromisoformat(day),root/'data',assessment_policy=PERIOD_INPUT_POLICY_V43)
    assert result['_daily_input_quality']['structural_valid'] and result['records']
    assert not any(d in result['_daily_input_quality']['defects'] for d in ('PERIOD_INPUT_JSON_UNAVAILABLE','PERIOD_INPUT_MARKDOWN_UNAVAILABLE'))
    assert result['_daily_input_quality']['independent_acceptance']=='UNKNOWN_NOT_EVALUATED'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
