import json
from pathlib import Path

import pytest
from lattice_digest import report_repair as repair
from lattice_digest.authority import INCOMPLETE_ZERO_TEXT, semantic_qa
from lattice_digest.promotion_history import load_promotion_history
from scripts.verify_durable_artifacts import verify_daily
from tests.test_runtime_isolation_v2 import nested_repo, published_repo, invoke


def candidate(root, target='2026-08-22'):
    scratch=root/'.ops/scratch/gap'
    payload=repair.prepare_missing_candidate(target)
    jp,mp=repair.pair_paths(scratch,'daily',target)
    jp.parent.mkdir(parents=True);mp.parent.mkdir(parents=True)
    md=repair.render_daily(payload,target)
    jp.write_text(json.dumps(payload),encoding='utf-8');mp.write_bytes(md)
    return payload, {'kind':'daily','target':target,'operation':'CREATE_INCOMPLETE_HISTORY',
        'candidate_root':str(scratch),'candidate_json_sha256':repair.digest(jp.read_bytes()),
        'candidate_markdown_sha256':repair.digest(md)}


def test_legacy_all_filtered_rows_still_render_incomplete_zero_caveat():
    row={'title':'Crystal lattice vibrations','abstract':'Phonon dynamics in crystals.',
         'source':'arxiv','source_url':'https://arxiv.org/abs/2609.31589v1'}
    payload=repair.prepare_legacy_candidate([row],'0'*64,'2026-09-25')
    md=repair.render_daily(payload,'2026-09-25').decode('utf-8')
    assert INCOMPLETE_ZERO_TEXT in md
    assert payload['records'][0]['relevance_label']=='D'
    assert semantic_qa(payload,md)['status']=='PASS'


def test_gap_creation_has_unknown_counts_no_events_and_no_prior_history(tmp_path):
    payload,item=candidate(tmp_path)
    result=repair.repair_pair(tmp_path,item,tmp_path/'.ops/evidence/tx',execute=True)
    assert result['status']=='PROMOTED_INCOMPLETE_HISTORY'
    jp,mp=repair.pair_paths(tmp_path,'daily',item['target'])
    assert json.loads(jp.read_bytes())==payload
    assert '原始发现数量 N/A' in mp.read_text(encoding='utf-8')
    assert '36' not in mp.read_text(encoding='utf-8')
    assert 'publication_event_ledger' not in payload and payload['records']==[]
    assert load_promotion_history(tmp_path/'data', __import__('datetime').date(2026,8,23))[0]==[]
    assert verify_daily(tmp_path,item['target'])['status']=='verified'


@pytest.mark.parametrize('field,value', [('coverage_start','2026-08-21T00:00:00Z'),
    ('coverage_end','2026-08-22T00:00:00Z'), ('run_date','2026-08-22'),('run_mode','backfill'),
    ('quality_status','authoritative'),('publication_policy_version','scientific-publication-p0'),
    ('original_failed_discovery_counts',0),('legacy_original_json_sha256','0'*64),
    ('original_execution_status','PASS'),('source_snapshot_kind','ORIGINAL'),
    ('original_requested_window',{'coverage_start':'invented'})])
def test_gap_cannot_upgrade_unknown_historical_facts(tmp_path,field,value):
    payload,item=candidate(tmp_path);payload['metadata'][field]=value
    jp,_=repair.pair_paths(Path(item['candidate_root']),'daily',item['target'])
    jp.write_text(json.dumps(payload),encoding='utf-8');item['candidate_json_sha256']=repair.digest(jp.read_bytes())
    with pytest.raises(ValueError,match='invented'):repair.repair_pair(tmp_path,item,tmp_path/'.ops/evidence/tx',execute=True)
    assert not repair.pair_paths(tmp_path,'daily',item['target'])[0].exists()


@pytest.mark.parametrize('key,value',[('records',[{'title':'invented'}]),('publication_event_ledger',{}),('source_health',[])])
def test_gap_cannot_contain_invented_papers_events_or_provider_health(tmp_path,key,value):
    payload,item=candidate(tmp_path);payload[key]=value
    jp,_=repair.pair_paths(Path(item['candidate_root']),'daily',item['target'])
    jp.write_text(json.dumps(payload),encoding='utf-8');item['candidate_json_sha256']=repair.digest(jp.read_bytes())
    with pytest.raises(ValueError,match='invented'):repair.repair_pair(tmp_path,item,tmp_path/'.ops/evidence/tx',execute=True)


@pytest.mark.parametrize('existing_index',[0,1])
def test_creation_never_overwrites_either_existing_target(tmp_path,existing_index):
    _,item=candidate(tmp_path);paths=repair.pair_paths(tmp_path,'daily',item['target'])
    p=paths[existing_index];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'USER ORIGINAL')
    with pytest.raises(ValueError,match='already exists'):repair.repair_pair(tmp_path,item,tmp_path/'.ops/evidence/tx',execute=True)
    assert p.read_bytes()==b'USER ORIGINAL' and not paths[1-existing_index].exists()


def test_second_install_failure_rolls_back_only_our_new_file(tmp_path,monkeypatch):
    paths=(tmp_path/'report.json',tmp_path/'report.md');actual=repair.os.link;calls=[]
    def fail(src,dst):
        calls.append(dst)
        if len(calls)==2:raise OSError('injected install failure')
        actual(src,dst)
    monkeypatch.setattr(repair.os,'link',fail)
    with pytest.raises(OSError):repair._create_missing(paths,(b'json',b'markdown'),tmp_path/'proof')
    assert not any(p.exists() for p in paths)
    assert json.loads((tmp_path/'proof/receipt.json').read_bytes())['state']=='ROLLED_BACK'


def test_concurrent_owner_is_preserved_and_our_first_install_is_removed(tmp_path,monkeypatch):
    paths=(tmp_path/'report.json',tmp_path/'report.md');actual=repair.os.link;calls=[]
    def drift(src,dst):
        calls.append(dst)
        if len(calls)==2:Path(dst).write_bytes(b'USER CONCURRENT')
        actual(src,dst)
    monkeypatch.setattr(repair.os,'link',drift)
    with pytest.raises(FileExistsError):repair._create_missing(paths,(b'json',b'markdown'),tmp_path/'proof')
    assert not paths[0].exists() and paths[1].read_bytes()==b'USER CONCURRENT'


def test_concurrent_edit_to_installed_file_is_not_deleted_on_rollback(tmp_path,monkeypatch):
    paths=(tmp_path/'report.json',tmp_path/'report.md');actual=repair.os.link;calls=[]
    def drift(src,dst):
        calls.append(dst)
        if len(calls)==2:
            paths[0].write_bytes(b'USER EDIT')
            raise OSError('injected failure after concurrent edit')
        actual(src,dst)
    monkeypatch.setattr(repair.os,'link',drift)
    with pytest.raises(OSError):repair._create_missing(paths,(b'json',b'markdown'),tmp_path/'proof')
    assert paths[0].read_bytes()==b'USER EDIT'
    assert json.loads((tmp_path/'proof/receipt.json').read_bytes())['state']=='ROLLBACK_BLOCKED_BY_CONCURRENT_CHANGE'


def test_actual_public_repair_cli_creates_only_explicit_incomplete_history(nested_repo):
    code,root,_=nested_repo
    _,item=candidate(root);evidence=root/'.ops/evidence';evidence.mkdir(parents=True)
    plan=evidence/'plan.json';plan.write_text(json.dumps([item]),encoding='utf-8')
    result=invoke(code,root,'lattice_digest.report_repair',['--plan',str(plan),'--plan-sha256',repair.digest(plan.read_bytes()),'--execute'])
    assert result.returncode==0,result.stdout+result.stderr
    receipt=json.loads((evidence/'plan-execution.json').read_bytes())
    assert receipt['runtime']['runtime_code_state']=='PUBLISHED_CLEAN_RUNTIME'
    assert receipt['results'][0]['status']=='PROMOTED_INCOMPLETE_HISTORY'
    assert verify_daily(root,item['target'])['status']=='verified'
