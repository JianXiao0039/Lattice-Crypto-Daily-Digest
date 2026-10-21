"""Optional post-canonical publication stage; no scheduler or canonical mutation."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
from pathlib import Path
from lattice_digest.report_gate import verify, encoded, GateError, fail, period_bounds
from lattice_digest.public_report import project, export, inspect_tree
from lattice_digest.public_publisher import publish
from lattice_digest.public_contract import public_preflight, _reject_redirects

REMOTE = 'https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git'


def deliver(root: Path, kind: str, period: str, *, remote: str = REMOTE,
            approved: bool = False, windows_credentials: bool = False) -> dict:
    if not approved:
        fail('PUBLICATION_NOT_APPROVED', 'reviewed continuing authorization is required')
    period_bounds(kind, period)
    directory = root/'audits/public-delivery'/kind/period
    _reject_redirects(directory)
    directory.mkdir(parents=True,exist_ok=True)
    lock = directory/'writer.lock'
    try: owner = lock.open('x',encoding='utf-8')
    except FileExistsError: fail('PUBLISH_CONFLICT','active or stale public delivery writer; inspect before recovery')
    receipt = {'schema_version':'public-delivery-v1','report_type':kind,'report_period':period,
               'states':[],'status':'STARTED'}
    def save():
        target=directory/'receipt.json';staged=directory/'receipt.staged'
        _reject_redirects(target);_reject_redirects(staged)
        with staged.open('w',encoding='utf-8') as stream:
            stream.write(encoded(receipt).decode());stream.flush();os.fsync(stream.fileno())
        os.replace(staged,target)
    try:
        with owner:
            owner.write(str(os.getpid()));owner.flush();os.fsync(owner.fileno())
            pair=verify(root,kind,period)
            receipt['states'] += ['CANONICAL_GENERATED','CANONICAL_QA_VERIFIED']
            public=project(pair)
            generation=public['public_generation_id']
            candidate=directory/generation
            _reject_redirects(candidate)
            if candidate.exists():
                manifest,files=inspect_tree(candidate)
                key=kind+':'+period
                if manifest['reports'].get(key,{}).get('public_generation_id')!=generation:
                    fail('PAIR_HASH_MISMATCH','saved candidate differs from verified canonical generation')
            else: export(root,kind,period,candidate)
            inspect_tree(candidate)
            receipt.update(source_generation_id=pair.payload['metadata']['generation_id'],
                           public_generation_id=generation, canonical_pair_sha256=public['canonical_pair_sha256'])
            receipt['states'] += ['PUBLIC_EXPORT_VERIFIED','PRIVACY_QA_VERIFIED']
            receipt['status']='PUBLISH_PENDING';save()
            try:
                result=publish(candidate,remote,approved=True,use_windows_credentials=windows_credentials,
                               accept_superseded=True)
            except (GateError,OSError,ValueError,subprocess.SubprocessError) as exc:
                receipt['error_code']=exc.code if isinstance(exc,GateError) else 'REMOTE_PUBLICATION_FAILED'
                save()
                return receipt
            if result['remote_readback']!='PASS':
                fail('REMOTE_READBACK_FAILED','publisher did not supply verified remote evidence')
            receipt['states'] += ['GITHUB_PUSH_VERIFIED','REMOTE_READBACK_VERIFIED']
            receipt.update(status=result['status'],remote_commit=result['commit'],publication=result)
            save()
            return receipt
    finally:
        lock.unlink(missing_ok=True)


def pending(root: Path, kind: str) -> list[str]:
    directory=root/'audits/public-delivery'/kind
    _reject_redirects(directory)
    result=[]
    for position,path in enumerate(sorted(directory.glob('*/receipt.json'),reverse=True)):
        if position>=64: break
        _reject_redirects(path)
        if path.stat().st_size>16384: fail('PAYLOAD_SIZE_INVALID','delivery receipt exceeds bound')
        period=path.parent.name;period_bounds(kind,period)
        value=json.loads(path.read_bytes())
        if value.get('report_type')!=kind or value.get('report_period')!=period:
            fail('PERIOD_IDENTITY_INVALID','pending receipt identity mismatch')
        if value.get('status')=='PUBLISH_PENDING': result.append(period)
        if len(result)==3: break
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--type',choices=('daily','weekly','monthly'),required=True)
    parser.add_argument('--period')
    parser.add_argument('--retry-pending',action='store_true')
    parser.add_argument('--approve-reviewed-publication',action='store_true')
    parser.add_argument('--use-windows-credentials',action='store_true')
    args=parser.parse_args(argv)
    try:
        if not args.approve_reviewed_publication:
            fail('PUBLICATION_NOT_APPROVED','explicit existing recurring publication authorization is required')
        paths,proof=public_preflight('PUBLIC_DELIVERY')
        targets=pending(paths.canonical_root,args.type) if args.retry_pending else []
        if args.period and args.period not in targets: targets.append(args.period)
        if not targets and not args.retry_pending:
            fail('PERIOD_IDENTITY_INVALID','explicit validated canonical report period is required')
        results=[deliver(paths.canonical_root,args.type,period,approved=True,
                         windows_credentials=args.use_windows_credentials) for period in targets]
        print(json.dumps({'runtime_head':proof['runtime_provenance']['runtime_git_head'],'deliveries':results}))
        return 2 if any(r['status']=='PUBLISH_PENDING' for r in results) else 0
    except (GateError,OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        print(json.dumps({'gate':'PUBLIC_EXPORT_AND_PUBLISH','status':'FAIL',
            'code':exc.code if isinstance(exc,GateError) else 'PUBLIC_DELIVERY_FAILED'}))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
