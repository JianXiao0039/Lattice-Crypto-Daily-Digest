import gzip
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from lattice_digest import report_repair as repair
from lattice_digest.authority import derive_authority, semantic_qa
from lattice_digest.storage import publish_daily_pair
from lattice_digest.weekly_synthesis import build_weekly_synthesis, render_markdown, _strip_private_weekly
from tests.test_nested_public_e2e import health, seed_days
from tests.test_runtime_isolation_v2 import nested_repo, published_repo, invoke


def test_pair_transaction_snapshots_are_exact_and_restorable(tmp_path):
    paths=tmp_path/'report.json',tmp_path/'report.md'
    original=b'{"historical": true}\r\n','# 原始\r\n'.encode('utf-8')
    for p,data in zip(paths,original):p.write_bytes(data)
    expected=tuple(repair.digest(x) for x in original)
    new=b'{"corrected": true}\n',b'# corrected\n'
    result=repair._promote(paths,new,expected,tmp_path/'receipt')
    assert result['state']=='PROMOTED'
    for name,data in zip(('original.json.gz','original.md.gz'),original):
        with gzip.open(tmp_path/'receipt'/name,'rb') as f:assert f.read()==data
    assert tuple(p.read_bytes() for p in paths)==new


def test_second_replacement_failure_rolls_back_first_and_retains_failure_receipt(tmp_path,monkeypatch):
    paths=tmp_path/'a.json',tmp_path/'a.md';original=(b'old-json',b'old-md')
    for p,data in zip(paths,original):p.write_bytes(data)
    actual=repair.os.replace;calls=[]
    def fail_once(src,dst):
        calls.append((src,dst))
        if len(calls)==2:raise OSError('test injected second replace failure')
        return actual(src,dst)
    monkeypatch.setattr(repair.os,'replace',fail_once)
    with pytest.raises(OSError):repair._promote(paths,(b'new-json',b'new-md'),tuple(map(repair.digest,original)),tmp_path/'proof')
    assert tuple(p.read_bytes() for p in paths)==original
    assert json.loads((tmp_path/'proof/receipt.json').read_text())['state']=='ROLLED_BACK'


def test_stale_original_guard_does_not_overwrite_or_snapshot(tmp_path):
    paths=tmp_path/'a.json',tmp_path/'a.md'
    for p in paths:p.write_bytes(b'changed since review')
    with pytest.raises(ValueError,match='hash changed'):
        repair._promote(paths,(b'new',b'new'),('0'*64,'0'*64),tmp_path/'proof')
    assert not (tmp_path/'proof').exists()
    assert all(p.read_bytes()==b'changed since review' for p in paths)


@pytest.mark.parametrize('kind,target',[('daily','../escape'),('weekly','2026-W99'),('monthly','2026-13'),('other','2026-10-12')])
def test_bad_targets_cannot_choose_arbitrary_paths(tmp_path,kind,target):
    with pytest.raises(ValueError):repair.pair_paths(tmp_path,kind,target)


def test_junction_candidate_escape_blocks(tmp_path):
    inside=tmp_path/'inside';outside=tmp_path/'outside';inside.mkdir();outside.mkdir()
    import os,subprocess
    if os.name!='nt':
        (inside/'redirect').symlink_to(outside,target_is_directory=True)
    else:
        assert subprocess.run(['cmd','/c','mklink','/J',str(inside/'redirect'),str(outside)],capture_output=True).returncode==0
    try:
        with pytest.raises(ValueError,match='redirect'):repair.checked_path(inside/'redirect/file',inside)
    finally:(inside/'redirect').rmdir() if os.name=='nt' else (inside/'redirect').unlink()


def make_legacy_empty(root,candidate_root):
    target='2025-01-02';old={'metadata':{'target_date':target,'run_date':'2026-06-22','since_window':'24h','quality_status':'provisional'},
        'records':[],'source_health':health(True),'warnings':[]}
    new=json.loads(json.dumps(old));meta=new['metadata'];meta.update(derive_authority([],new['source_health']))
    meta.update(generation_id='repair-test',source_starved=False,publication_event_semantics='UNRESOLVED_LEGACY_WINDOW')
    md=repair.render_daily(new,target);meta['markdown_sha256']=repair.digest(md)
    meta['semantic_qa']={k:v for k,v in semantic_qa(new,md.decode(),candidate=True).items() if k!='derived_authority'}
    for base,payload,text in ((root,old,b'# original no-news\n'),(candidate_root,new,md)):
        jp,mp=repair.pair_paths(base,'daily',target);jp.parent.mkdir(parents=True);mp.parent.mkdir(parents=True)
        jp.write_text(json.dumps(payload),encoding='utf-8');mp.write_bytes(text)
    paths=repair.pair_paths(root,'daily',target);candidates=repair.pair_paths(candidate_root,'daily',target)
    item={'kind':'daily','target':target,'candidate_root':str(candidate_root),
        'original_json_sha256':repair.digest(paths[0].read_bytes()),'original_markdown_sha256':repair.digest(paths[1].read_bytes()),
        'candidate_json_sha256':repair.digest(candidates[0].read_bytes()),'candidate_markdown_sha256':repair.digest(candidates[1].read_bytes())}
    return old,new,md,item


def test_legacy_empty_claim_repair_does_not_invent_event_ledger_or_source_window(tmp_path):
    candidate=tmp_path/'.ops/scratch/candidate';old,new,md,item=make_legacy_empty(tmp_path,candidate)
    result=repair.repair_pair(tmp_path,item,tmp_path/'.ops/evidence/repairs',execute=True)
    assert result['status']=='PROMOTED' and result['qa']['durable']=='PASS'
    stored=json.loads(repair.pair_paths(tmp_path,'daily','2025-01-02')[0].read_text())
    assert 'publication_event_ledger' not in stored and 'coverage_start' not in stored['metadata']
    assert stored['metadata']['run_date']==old['metadata']['run_date']
    assert stored['source_health']==old['source_health']
    assert not list((tmp_path/'data').rglob('*.lock'))


@pytest.mark.parametrize('mutation',['source_timestamp','source_health','coverage','unreviewed_prose','candidate_hash'])
def test_candidate_tampering_blocks_without_canonical_mutation(tmp_path,mutation):
    candidate=tmp_path/'.ops/scratch/candidate';old,new,md,item=make_legacy_empty(tmp_path,candidate)
    paths=repair.pair_paths(tmp_path,'daily',item['target']);before=tuple(p.read_bytes() for p in paths)
    cp=repair.pair_paths(candidate,'daily',item['target'])
    if mutation=='source_timestamp':new['records']=[{'title':'fabricated','source':'arxiv','source_url':'https://arxiv.org/abs/9999.99999','publication_date':'2025-01-02'}]
    if mutation=='source_health':new['source_health'][0]['runtime_state']='complete'
    if mutation=='coverage':new['metadata']['coverage_start']='2025-01-01T00:00:00Z'
    if mutation=='unreviewed_prose':md+=b'Unsupported result claim\n'
    cp[0].write_text(json.dumps(new),encoding='utf-8');cp[1].write_bytes(md)
    if mutation!='candidate_hash':
        item['candidate_json_sha256']=repair.digest(cp[0].read_bytes());item['candidate_markdown_sha256']=repair.digest(md)
    else:cp[0].write_bytes(cp[0].read_bytes()+b' ')
    with pytest.raises(ValueError):repair.repair_pair(tmp_path,item,tmp_path/'.ops/evidence/repairs',execute=True)
    assert tuple(p.read_bytes() for p in paths)==before


def test_weekly_candidate_is_derived_from_original_inputs_and_never_upgrades_degraded_coverage(tmp_path):
    root=tmp_path/'canonical';candidate=root/'.ops/scratch/candidate';start=date(2025,12,29)
    seed_days(root,start,7,degraded_day=2)
    import shutil
    shutil.copytree(root/'data',candidate/'data');shutil.copytree(root/'digests',candidate/'digests')
    payload=build_weekly_synthesis(root/'data',start,start+timedelta(days=6))
    stripped=_strip_private_weekly(payload)
    md=(render_markdown(payload)+repair.REPAIR_NOTE).encode()
    jp,mp=repair.pair_paths(candidate,'weekly',payload['week_id']);jp.parent.mkdir(parents=True);mp.parent.mkdir(parents=True)
    jp.write_text(json.dumps(stripped),encoding='utf-8');mp.write_bytes(md)
    result=repair.validate_candidate(root,candidate,'weekly',payload['week_id'],{},stripped,md)
    assert result['authority_state']=='AUTHORITATIVE_DEGRADED'
    stripped['coverage']['authority_state']='AUTHORITATIVE_COMPLETE'
    with pytest.raises(ValueError):repair.validate_candidate(root,candidate,'weekly',payload['week_id'],{},stripped,md)


def test_actual_repair_cli_uses_clean_nested_test_authority_and_guarded_plan(nested_repo):
    code,canonical,_=nested_repo
    candidate=canonical/'.ops/scratch/repaired-pair'
    _,_,_,item=make_legacy_empty(canonical,candidate)
    evidence=canonical/'.ops/evidence';evidence.mkdir(parents=True)
    plan=evidence/'plan.json';plan.write_text(json.dumps([item]),encoding='utf-8')
    result=invoke(code,canonical,'lattice_digest.report_repair',
                  ['--plan',str(plan),'--plan-sha256',repair.digest(plan.read_bytes()),'--execute'])
    assert result.returncode==0,result.stdout+result.stderr
    receipt=json.loads((evidence/'plan-execution.json').read_text())
    assert receipt['runtime']['runtime_code_state']=='PUBLISHED_CLEAN_RUNTIME'
    assert receipt['results'][0]['status']=='PROMOTED'
    assert receipt['results'][0]['qa']['authority_state']=='INCOMPLETE_DO_NOT_INTERPRET_AS_NO_NEWS'


def test_windows_source_warning_newlines_do_not_break_durable_pair_hash(tmp_path):
    candidate=tmp_path/'.ops/scratch/candidate';old,new,_,item=make_legacy_empty(tmp_path,candidate)
    old['warnings']=['Original Windows diagnostic\r\nsecond line']
    new['warnings']=old['warnings'][:]
    md=repair.render_daily(new,item['target']);assert b'\r' not in md
    new['metadata']['markdown_sha256']=repair.digest(md)
    paths=repair.pair_paths(tmp_path,'daily',item['target']);cp=repair.pair_paths(candidate,'daily',item['target'])
    paths[0].write_text(json.dumps(old),encoding='utf-8');cp[0].write_text(json.dumps(new),encoding='utf-8');cp[1].write_bytes(md)
    item['original_json_sha256']=repair.digest(paths[0].read_bytes());item['candidate_json_sha256']=repair.digest(cp[0].read_bytes());item['candidate_markdown_sha256']=repair.digest(md)
    assert repair.repair_pair(tmp_path,item,tmp_path/'.ops/evidence/repairs',execute=True)['status']=='PROMOTED'
