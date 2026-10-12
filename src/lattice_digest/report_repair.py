"""Owner-only, hash-guarded replacement of evidence-derived report pairs.

No discovery, database writes, scheduler changes or implicit legacy conversion.
Per-file replacement is atomic; ordinary I/O failure rolls back both files.
A journal and pair hash make a crash between replacements detectable.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4
from zoneinfo import ZoneInfo

from lattice_digest.artifact_paths import daily_data_path, daily_digest_path, weekly_data_path, weekly_digest_path, monthly_data_path, monthly_digest_path
from lattice_digest.authority import semantic_qa
from lattice_digest.digest import generate_markdown
from lattice_digest.models import PaperRecord
from lattice_digest.promotion_history import load_promotion_history, classify_event
from lattice_digest.public_contract import public_preflight, _reject_redirects
from lattice_digest.runtime_provenance import runtime_provenance, public_runtime_allowed
from lattice_digest.weekly_synthesis import build_weekly_synthesis, render_markdown as render_weekly, _strip_private_weekly
from lattice_digest.monthly_synthesis import build_monthly_synthesis, render_markdown as render_monthly
from scripts.verify_durable_artifacts import verify_daily, verify_weekly, verify_monthly

SOURCE_FIELDS = ('title','authors','abstract','conclusion','source','source_url','source_urls','paper_id','doi','arxiv_id','eprint_id','venue',
    'publication_date','publication_timestamp','publication_date_kind','preprint_first_posted_at','announcement_date','announcement_timestamp',
    'update_date','update_timestamp','update_date_kind','source_version_timestamp','first_seen_at','first_seen_date')
REPAIR_NOTE = '\n\n<!-- verified-report-repair -->\n- 历史报告修复：保留原始来源记录与观察时间；缺失的旧版出版事件证据仍为 UNKNOWN，不能视为新观察的当前模式事实。\n'

def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def pair_paths(root: Path, kind: str, target: str) -> tuple[Path, Path]:
    if kind == 'daily':
        day = date.fromisoformat(target)
        return daily_data_path(day,root/'data'), daily_digest_path(day,root/'digests')
    if kind == 'weekly':
        year, week = map(int,target.split('-W'))
        date.fromisocalendar(year,week,1)
        return weekly_data_path(target,root=root/'data'), weekly_digest_path(target,root=root/'digests')
    if kind == 'monthly':
        datetime.strptime(target,'%Y-%m')
        return monthly_data_path(target,root=root/'data'), monthly_digest_path(target,root=root/'digests')
    raise ValueError('unsupported report kind')

def checked_path(path: Path, within: Path) -> Path:
    path=path.absolute()
    _reject_redirects(path)
    if not path.resolve().is_relative_to(within.resolve()):
        raise ValueError('repair path escapes authorized root')
    return path

def render_daily(payload: dict, target: str) -> bytes:
    meta=payload['metadata']
    rows=[PaperRecord(**{k:v for k,v in row.items() if k in PaperRecord.model_fields}) for row in payload['records']]
    rendered=generate_markdown(rows,date.fromisoformat(target),int(meta.get('filtered_count',0)),
        payload.get('source_health',[]),payload.get('warnings',[]),meta.get('since_window','36h'),
        {**meta,'_publication_payload':payload})
    rendered+=f"\n<!-- generation:{meta['generation_id']} -->\n"
    # Source warnings can contain Windows CRLF. Preserve their original JSON
    # bytes, but publish a single Markdown newline convention for hash readers.
    return (rendered+REPAIR_NOTE).replace('\r\n','\n').replace('\r','\n').encode('utf-8')

def _source_projection(rows):
    return [{k:r[k] for k in SOURCE_FIELDS if k in r} for r in rows]

def validate_candidate(root: Path, candidate_root: Path, kind: str, target: str, original: dict, candidate: dict, markdown: bytes) -> dict:
    if kind=='daily':
        if not isinstance(original,dict) or not isinstance(original.get('records'),list):
            raise ValueError('unreconciled legacy schema cannot be automatically repaired')
        if _source_projection(original['records']) != _source_projection(candidate.get('records',[])):
            raise ValueError('source records, identities or timestamps changed')
        if original.get('source_health',[]) != candidate.get('source_health',[]):
            raise ValueError('original provider health changed')
        old=original.get('metadata',{});meta=candidate.get('metadata',{})
        for key in ('coverage_start','coverage_end','publication_policy_version','quality_status','run_date','run_mode'):
            if old.get(key)!=meta.get(key):raise ValueError('original coverage or policy changed: '+key)
        if meta.get('target_date')!=target:raise ValueError('candidate target date mismatch')
        if markdown!=render_daily(candidate,target):raise ValueError('candidate Markdown is not the authorized renderer output')
        qa=semantic_qa(candidate,markdown.decode('utf-8'))
        if qa['status']!='PASS':raise ValueError('candidate semantic QA failed: '+json.dumps(qa))
        prior=[]
        if any(r.get('primary_today_new_eligible') for r in candidate['records']):
            prior,_=load_promotion_history(root/'data',date.fromisoformat(target))
        for row in candidate['records']:
            event,_=classify_event(row,prior)
            if row.get('primary_today_new_eligible') and event!='NEW_DISTINCT_PAPER' and row.get('publication_event_type')!='primary_publication_events':
                raise ValueError('cross-day false primary')
        durable=verify_daily(candidate_root,target)
    else:
        if kind=='weekly':
            year,week=map(int,target.split('-W'));start=date.fromisocalendar(year,week,1)
            expected=_strip_private_weekly(build_weekly_synthesis(root/'data',start,start+timedelta(days=6),datetime.fromisoformat(candidate['generated_at'])))
            render=render_weekly;durable=verify_weekly(candidate_root,target)
        else:
            first=datetime.strptime(target,'%Y-%m').date()
            today=datetime.now(ZoneInfo('Asia/Singapore')).date()
            following=first.replace(year=first.year+1,month=1) if first.month==12 else first.replace(month=first.month+1)
            if following>today:raise ValueError('monthly period has not ended')
            expected=build_monthly_synthesis(root/'data',target,generated_at=datetime.fromisoformat(candidate['generated_at']))
            render=render_monthly;durable=verify_monthly(candidate_root,target)
        proposed={k:v for k,v in candidate.items() if k not in ('metadata','repair_receipt')}
        actual={k:v for k,v in expected.items() if k not in ('metadata','repair_receipt')}
        if proposed!=actual:raise ValueError('period data differs from current canonical input derivation')
        if markdown!=(render(expected)+REPAIR_NOTE).encode('utf-8'):
            raise ValueError('period Markdown differs from source-derived renderer')
        qa=durable.get('semantic_qa',{})
    if durable.get('status')!='verified':raise ValueError('durable verifier failed: '+json.dumps(durable))
    return {'structural':'PASS','semantic':qa['status'],'cross_day':'PASS','durable':'PASS',
            'authority_state':durable.get('authority_state')}

def _promote(paths: tuple[Path,Path], contents: tuple[bytes,bytes], expected: tuple[str,str], evidence: Path) -> dict:
    original=tuple(p.read_bytes() for p in paths)
    if tuple(map(digest,original))!=expected:raise ValueError('original pair hash changed; refuse replacement')
    evidence.mkdir(parents=True,exist_ok=False)
    for name,data in zip(('original.json.gz','original.md.gz'),original):
        with gzip.open(evidence/name,'wb') as stream:stream.write(data)
        with gzip.open(evidence/name,'rb') as stream:
            if stream.read()!=data:raise ValueError('original snapshot restoration failed')
    journal={'state':'PREPARED','targets':[str(p) for p in paths],'original_sha256':list(expected),
             'candidate_sha256':list(map(digest,contents)),'pair_atomicity':'PER_FILE_ATOMIC; JOURNALED_PAIR; ORDINARY_ERROR_ROLLBACK'}
    receipt=evidence/'receipt.json';receipt.write_text(json.dumps(journal,indent=2),encoding='utf-8')
    temps=[];promoted=[]
    try:
        for p,data in zip(paths,contents):
            fd,name=tempfile.mkstemp(prefix='.report-repair-',dir=p.parent);temps.append(Path(name))
            with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        if tuple(digest(p.read_bytes()) for p in paths)!=expected:raise ValueError('pair changed during candidate staging')
        for index,(temp,p) in enumerate(zip(temps,paths)):
            os.replace(temp,p);promoted.append(index)
        if tuple(digest(p.read_bytes()) for p in paths)!=tuple(map(digest,contents)):raise OSError('promoted pair verification failed')
    except (OSError,ValueError):
        for index in reversed(promoted):
            fd,name=tempfile.mkstemp(prefix='.report-rollback-',dir=paths[index].parent)
            with os.fdopen(fd,'wb') as stream:stream.write(original[index]);stream.flush();os.fsync(stream.fileno())
            os.replace(name,paths[index])
        journal['state']='ROLLED_BACK';receipt.write_text(json.dumps(journal,indent=2),encoding='utf-8')
        raise
    finally:
        for p in temps:p.unlink(missing_ok=True)
    journal['state']='PROMOTED';receipt.write_text(json.dumps(journal,indent=2),encoding='utf-8')
    return journal

def repair_pair(root: Path, item: dict, evidence_root: Path, *, execute: bool=False) -> dict:
    kind,target=item['kind'],item['target'];paths=pair_paths(root,kind,target)
    for p in paths:checked_path(p,root)
    candidate_root=checked_path(Path(item['candidate_root']),root/'.ops/scratch')
    candidates=pair_paths(candidate_root,kind,target)
    for p in candidates:checked_path(p,candidate_root)
    expected=(item['original_json_sha256'],item['original_markdown_sha256'])
    checked_path(evidence_root,root/'.ops/evidence')
    contents=tuple(p.read_bytes() for p in candidates)
    if tuple(map(digest,contents))!=(item['candidate_json_sha256'],item['candidate_markdown_sha256']):
        raise ValueError('candidate hash mismatch')
    lock=paths[0].with_name('.'+paths[0].stem+'.report-repair.lock')
    _reject_redirects(lock)
    stream=lock.open('x',encoding='utf-8')
    try:
        with stream:
            original=json.loads(paths[0].read_bytes());candidate=json.loads(contents[0])
            if tuple(digest(p.read_bytes()) for p in paths)!=expected:raise ValueError('original pair hash mismatch')
            checks=validate_candidate(root,candidate_root,kind,target,original,candidate,contents[1])
            if not execute:return {'kind':kind,'target':target,'status':'QA_PASSED_NOT_PROMOTED','qa':checks}
            result=_promote(paths,contents,expected,evidence_root/(kind+'-'+target+'-'+uuid4().hex))
            return {'kind':kind,'target':target,'status':'PROMOTED','qa':checks,**result}
    finally:lock.unlink(missing_ok=True)

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args(argv)
    paths,proof=public_preflight('REPORT_REPAIR')
    plan=checked_path(args.plan,paths.canonical_root/'.ops/evidence');content=plan.read_bytes()
    if digest(content)!=args.plan_sha256:raise ValueError('repair plan hash mismatch')
    items=json.loads(content)
    if not isinstance(items,list) or not items:raise ValueError('empty/invalid repair plan')
    evidence=checked_path(plan.parent/'transactions',paths.canonical_root/'.ops/evidence')
    results=[]
    for item in items:
        try:results.append(repair_pair(paths.canonical_root,item,evidence,execute=args.execute))
        except (OSError,ValueError,KeyError,TypeError) as exc:
            results.append({'kind':item.get('kind'),'target':item.get('target'),'status':'BLOCKED','error':type(exc).__name__+': '+str(exc)})
    target=plan.with_name(plan.stem+('-execution' if args.execute else '-preflight')+'.json')
    target.write_text(json.dumps({'runtime':proof['runtime_provenance'],'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'items':len(results),'promoted':sum(r['status']=='PROMOTED' for r in results),'blocked':sum(r['status']=='BLOCKED' for r in results),'receipt':str(target)}))
    return 1 if any(r['status']=='BLOCKED' for r in results) else 0

if __name__=='__main__':raise SystemExit(main())
