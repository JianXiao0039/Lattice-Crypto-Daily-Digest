"""Actual public entries with real saved inputs, isolated TEST Git authority.

No live provider completeness claim: Daily replaces only discovery transport with
the complete saved October18 source population. Renderer, SQLite, provenance,
source ranking, event ledger, pair publication and QA all execute normally.
"""
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
import hashlib,json,os,subprocess,sys,shutil
import pytest
from tests.test_runtime_isolation_v2 import published_repo

CAN=Path(r'D:\Code\CodexProjects\lattice-crypto-daily-digest')
PRODUCTION_PYTHON=Path(r'D:\CyberSecurity\Python313\python.exe')
PERIODS={'daily':('2026-10-04','2026-10-17'),'weekly':('2026-10-05','2026-10-11'),
         'monthly':('2026-09-01','2026-09-30')}


def required_history_inputs(kind, source_root):
    """Availability only; content and historical coverage remain actual assertions."""
    low,high=map(date.fromisoformat,PERIODS[kind]);inputs=[]
    day=low
    while day<=high:
        for part,ext in [('data','json'),('digests','md')]:
            inputs.append(source_root/part/'2026/daily'/f'{day}.{ext}')
        day+=timedelta(days=1)
    if kind=='daily':inputs.append(source_root/'data/2026/daily/2026-10-18.json')
    return inputs


def history_unavailable_reason(kind, *, source_root=CAN, python=PRODUCTION_PYTHON):
    if not python.is_file():
        return 'Real historical E2E unavailable: approved local production Python 3.13 is not installed.'
    missing=[p for p in required_history_inputs(kind,source_root) if not p.is_file()]
    if missing:
        return f'Real historical {kind} E2E unavailable: {len(missing)} required local input files are absent; CI does not contain the canonical historical corpus.'
    return None


def history_case(kind, *, source_root=CAN, python=PRODUCTION_PYTHON):
    # Param-level skip is decided before published_repo or any other fixture runs.
    reason=history_unavailable_reason(kind,source_root=source_root,python=python)
    return pytest.param(kind,marks=pytest.mark.skipif(reason is not None,
        reason=reason or 'Historical runtime and corpus are available.'))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seed(target,low,high):
    rows=[]
    for part,ext in [('data','json'),('digests','md')]:
        for p in sorted((CAN/part/'2026/daily').glob('*.'+ext)):
            if low<=p.stem<=high:
                to=target/p.relative_to(CAN);to.parent.mkdir(parents=True,exist_ok=True)
                # Independent bytes: scratch writes must not alias canonical evidence.
                shutil.copy2(p,to)
                rows.append({'source':str(p),'sha256':sha(p),'snapshot':str(to)})
    return rows

@pytest.mark.parametrize('kind',[history_case(kind) for kind in PERIODS])
def test_real_history_public_entry(published_repo,tmp_path,kind):
    code,_=published_repo
    E=tmp_path/'execution-evidence';E.mkdir()
    canonical=tmp_path/'canonical';canonical.mkdir()
    target={'daily':'2026-10-18','weekly':'2026-W41','monthly':'2026-09'}[kind]
    lo,hi=PERIODS[kind]
    inputs=seed(canonical,lo,hi)
    env={k:v for k,v in os.environ.items() if not k.startswith('LATTICE_DIGEST_')}
    env.update(PYTHONPATH=str(code/'src'),PYTHONDONTWRITEBYTECODE='1',
        LATTICE_DIGEST_CANONICAL_ROOT=str(canonical))
    python=str(PRODUCTION_PYTHON)
    module='lattice_digest.public_'+kind
    args={'weekly':['--from-date','2026-10-05','--to-date','2026-10-11'],
          'monthly':['--month','2026-09']} .get(kind)
    snapshot=CAN/'data/2026/daily/2026-10-18.json'
    if kind=='daily':
        meta=json.loads(snapshot.read_bytes())['metadata']
        args=['--run-mode','backfill','--quality-status','authoritative_backfill',
            '--target-date',target,'--coverage-start',meta['coverage_start'],'--coverage-end',meta['coverage_end'],
            '--original-missing-reason','V3_ISOLATED_RETROSPECTIVE_SAVED_SOURCE_REPLAY; no original-time collection claim',
            '--output','markdown,json','--send','none']
        inputs.append({'source':str(snapshot),'sha256':sha(snapshot),'role':'complete saved source population; original timestamps retained'})
    precommand=[python,'-m',module,'--preflight',*args]
    pre=subprocess.run(precommand,cwd=code,env=env,capture_output=True,text=True,encoding='utf-8')
    (E/f'{kind}-real-preflight.log').write_text(pre.stdout+pre.stderr,encoding='utf-8')
    assert pre.returncode==0,pre.stdout+pre.stderr
    command=[python,'-m',module,*args]
    if kind=='daily':
        script='''import json,sys,socket,dataclasses
from lattice_digest import run
from lattice_digest.models import PaperRecord
from lattice_digest.public_daily import main
snapshot=json.load(open(SNAPSHOT,encoding='utf-8'))
def deny(*a,**k):raise RuntimeError('NETWORK_DENIED_IN_SAVED_SOURCE_REPLAY')
socket.socket.connect=deny
def collect(configs,ctx):
 for config in configs:
  ctx.register_source(config);health=ctx.health(config['name'])
  saved=next((h for h in snapshot['source_health'] if h['source']==config['name']),{})
  for f in dataclasses.fields(health):
   if f.name!='name' and f.name in saved:setattr(health,f.name,saved[f.name])
  health.runtime_state='partial';health.runtime_reason_code='SAVED_SOURCE_REPLAY_NOT_FRESH_COLLECTION'
 ctx.query_attempts=snapshot['metadata'].get('source_query_runtime',[])
 ctx.warnings.append('RETROSPECTIVE_SAVED_SOURCE_REPLAY; original failures retained; no original-time completeness claim')
 return [PaperRecord(**{k:v for k,v in r.items() if k in PaperRecord.model_fields}) for r in snapshot['records']]
run._collect_records=collect
sys.exit(main(ARGS))
'''.replace('SNAPSHOT',repr(str(snapshot))).replace('ARGS',repr(args))
        script_path=E/'daily-real-executed.py';script_path.write_text(script,encoding='utf-8')
        command=[python,'-c',script]
    began=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(command,cwd=code,env=env,capture_output=True,text=True,encoding='utf-8',timeout=1800)
    (E/f'{kind}-real-execution.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    jp=canonical/f'data/2026/{kind}/{target}.json';mp=canonical/f'digests/2026/{kind}/{target}.md'
    receipt={'kind':kind,'target':target,'input_root':str(canonical),'inputs':inputs,
        'source_base_head':subprocess.check_output(['git','rev-parse','HEAD'],
            cwd=Path(__file__).resolve().parents[1],text=True).strip(),
        'test_authority_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=code,text=True).strip(),
        'authority_kind':'DISPOSABLE_LOCAL_TEST_AUTHORITY_NOT_PRODUCTION_DEPLOYMENT',
        'preflight_command':precommand,'preflight_exit':pre.returncode,
        'command':command if kind!='daily' else [python,str(E/'daily-real-executed.py')],
        'actual_started_at':began,'exit_code':result.returncode,
        'transport':'COMPLETE_REAL_SAVED_SOURCE_REPLAY_NETWORK_DENIED' if kind=='daily' else 'UNMOCKED_REAL_CANONICAL_DAILY_INPUTS',
        'files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in (jp,mp) if p.exists()]}
    if result.returncode==0:
        payload=json.loads(jp.read_bytes());markdown=mp.read_text('utf-8')
        if kind=='daily':
            from lattice_digest.authority import semantic_qa
            receipt['semantic_qa']=semantic_qa(payload,markdown)
            receipt['source_status']=payload['metadata']['authority_state']
            receipt['late_discoveries']=len(payload.get('late_arrivals',[]))
            required={'eprint:2026/2500','eprint:2026/2501','eprint:2026/2507','eprint:2026/2513'}
            assert required <= {x['canonical_identity'] for x in payload.get('late_arrivals',[])}
        else:
            from lattice_digest.period_delivery import verify_period_pair
            receipt['pair_integrity_qa']=verify_period_pair(jp,mp)
            receipt['source_status']=(payload.get('coverage') or payload.get('input_quality') or {}).get('authority_state')
            views=payload['publication_event_views']
            assert all(len({x['event_id'] for x in es})==len(es) for es in views['collections'].values())
            assert all(views['counts'][name]==len(es) for name,es in views['collections'].items())
            receipt['event_identity_count_qa']='PASS'
        # Original immutable history remains untouched; prove all input hashes again.
        receipt['input_hash_qa']='PASS' if all(sha(Path(x['source']))==x['sha256'] for x in inputs) else 'FAIL'
    (E/f'{kind}-real-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    if kind in ('daily','weekly'):
        # Daily's October 17 input has no original observations. The Weekly
        # fixture has only its bounded period corpus, not prior-day ownership
        # history. Both can create diagnostic pairs but cannot establish delivery.
        validation=json.loads((canonical/f'audits/generation-validation/{kind}/{target}/receipt.json').read_bytes())
        assert result.returncode==2,result.stdout+result.stderr
        assert validation['status']=='HISTORY_EVIDENCE_BLOCKED'
        assert validation['error_code']=='HISTORY_EVIDENCE_UNUSABLE'
        assert not validation['scientific_validation_verified']
        assert not validation['publish_pending'] and not validation['delivery_verified']
        assert len(receipt['files'])==2
        assert all(sha(Path(x['source']))==x['sha256'] for x in inputs)
        return
    assert result.returncode==0,result.stdout+result.stderr
    assert len(receipt['files'])==2
    assert receipt['input_hash_qa']=='PASS'
    if kind=='daily':assert receipt['semantic_qa']['status']=='PASS'
