from pathlib import Path
import copy
import hashlib
import json
from uuid import uuid4
import pytest
from lattice_digest import report_repair as repair

def candidate(root):
    payload={'generated_at':'2026-10-19T10:30:00+08:00','coverage':{'authority_state':'AUTHORITATIVE_DEGRADED'},
             'publication_event_views':{'collections':{},'counts':{}},'metadata':{'generation_id':uuid4().hex}}
    render=lambda p:'# 周报\n\n原始来源证据保留。\n'
    md=repair.render_period_repair(payload,render)
    payload['metadata']['markdown_sha256']=hashlib.sha256(md).hexdigest()
    payload['metadata']['payload_content_sha256']=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    j,m=repair.pair_paths(root,'weekly','2026-W42');j.parent.mkdir(parents=True);m.parent.mkdir(parents=True);j.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8');m.write_bytes(md)
    return payload,md,render

def setup_verifiers(monkeypatch,payload,render):
    expected={k:v for k,v in payload.items() if k!='metadata'}
    monkeypatch.setattr(repair,'build_weekly_synthesis',lambda *a,**kw:copy.deepcopy(expected))
    monkeypatch.setattr(repair,'render_weekly',render)
    monkeypatch.setattr(repair,'verify_weekly',lambda *a:{'status':'verified','semantic_qa':{'status':'PASS'},'authority_state':'AUTHORITATIVE_DEGRADED'})

def test_generation_pair_repair_passes_both_derivation_and_actual_durable_hash_gate(tmp_path,monkeypatch):
    p,md,render=candidate(tmp_path);setup_verifiers(monkeypatch,p,render)
    original={'metadata':{'generation_id':uuid4().hex}}
    assert repair.validate_candidate(tmp_path,tmp_path,'weekly','2026-W42',original,p,md)['durable']=='PASS'

@pytest.mark.parametrize('field',['markdown_sha256','payload_content_sha256'])
def test_tampered_pair_hash_is_not_hidden_by_period_derivation_qa(tmp_path,monkeypatch,field):
    p,md,render=candidate(tmp_path);setup_verifiers(monkeypatch,p,render)
    j,_=repair.pair_paths(tmp_path,'weekly','2026-W42');tampered=copy.deepcopy(p);tampered['metadata'][field]='0'*64;j.write_text(json.dumps(tampered),encoding='utf-8')
    with pytest.raises(ValueError,match='hash mismatch'):
        repair.validate_candidate(tmp_path,tmp_path,'weekly','2026-W42',{},tampered,md)

def test_modern_pair_cannot_be_downgraded_to_legacy_without_generation(tmp_path,monkeypatch):
    p,md,render=candidate(tmp_path);setup_verifiers(monkeypatch,p,render);p['metadata']={}
    with pytest.raises(ValueError,match='cannot discard generation'):
        repair.validate_candidate(tmp_path,tmp_path,'weekly','2026-W42',{'metadata':{'generation_id':uuid4().hex}},p,md)


def test_clean_disk_pair_cannot_validate_different_cached_promotion_payload(tmp_path,monkeypatch):
    p,md,render=candidate(tmp_path);setup_verifiers(monkeypatch,p,render)
    tampered=copy.deepcopy(p);tampered['metadata']['payload_content_sha256']='0'*64
    with pytest.raises(ValueError,match='differ from validated promotion contents'):
        repair.validate_candidate(tmp_path,tmp_path,'weekly','2026-W42',{},tampered,md)


def test_disk_markdown_change_cannot_validate_cached_promotion_bytes(tmp_path,monkeypatch):
    p,md,render=candidate(tmp_path);setup_verifiers(monkeypatch,p,render)
    _,m=repair.pair_paths(tmp_path,'weekly','2026-W42');m.write_bytes(md+b'changed')
    with pytest.raises(ValueError,match='differ from validated promotion contents'):
        repair.validate_candidate(tmp_path,tmp_path,'weekly','2026-W42',{},p,md)

def test_generation_marker_cannot_inject_markdown_or_html():
    with pytest.raises(ValueError,match='invalid period repair generation'):
        repair.render_period_repair({'metadata':{'generation_id':'bad --> <script>'}},lambda p:'# 周报\n')

@pytest.mark.parametrize('newline',['\n','\r\n'])
def test_legacy_period_rendering_remains_byte_compatible(newline):
    render=lambda p:'# 旧周报'+newline
    assert repair.render_period_repair({},render)==(render({})+repair.REPAIR_NOTE).encode()
