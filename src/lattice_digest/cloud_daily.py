"""Cloud-only provisional Daily candidate with a bounded scheduler target rule."""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from lattice_digest.report_gate import fail, GateError, encoded


def resolve_target(event_created_at: str, actual_start: str, trigger: str, target: str | None = None) -> dict:
    try:
        event = datetime.fromisoformat(event_created_at.replace('Z','+00:00'))
        actual = datetime.fromisoformat(actual_start.replace('Z','+00:00'))
        if not event.tzinfo or not actual.tzinfo or not timedelta(0) <= actual-event <= timedelta(hours=12):
            raise ValueError
        if trigger == 'schedule' and target is None:
            # GitHub created_at is the verified run event clock, not an exact cron execution.
            nominal = event.astimezone(timezone.utc).replace(hour=1,minute=17,second=0,microsecond=0)
            if nominal > event:
                nominal -= timedelta(days=1)
            if actual-nominal > timedelta(hours=12):
                raise ValueError
        elif trigger == 'workflow_dispatch' and target:
            from datetime import date
            day = date.fromisoformat(target)
            nominal = datetime.combine(day,datetime.min.time(),timezone.utc).replace(hour=1,minute=17)
            if not timedelta(0) <= actual-nominal <= timedelta(hours=36):
                raise ValueError
        else:
            raise ValueError
    except (ValueError, TypeError):
        fail('TARGET_DATE_RECOVERY_REQUIRED', 'scheduler target unresolved or outside bounded recovery; explicit reviewed recovery required')
    cutoff = nominal.astimezone(ZoneInfo('Asia/Singapore'))
    return {'schema_version':'cloud-target-v1','scheduler_event_time':event.isoformat(),
        'actual_start':actual.isoformat(),
        'collection_timing_source':'canonical metadata.source_query_runtime and runtime journal; not inferred from process start',
        'scheduled_for':cutoff.isoformat(),'target_date':str(cutoff.date()),
        'coverage_start':(cutoff-timedelta(hours=36)).isoformat(),'coverage_end':cutoff.isoformat(),
        'trigger':trigger,'target_resolution':'NOMINAL_CRON_WITH_12H_BOUND' if trigger=='schedule' else 'EXPLICIT_BOUNDED_MANUAL_TARGET'}


def execution_receipt(target: dict, metadata: dict) -> dict:
    # A new allowlisted operational clock record; never copy queries or headers.
    attempts=metadata.get('source_query_runtime',[])
    if not isinstance(attempts,list) or len(attempts)>2000:
        fail('SCHEMA_INVALID','cloud execution timing exceeds bounded attempt contract')
    starts=[];ends=[]
    for attempt in attempts:
        if not isinstance(attempt,dict): continue
        for field,values in [('started_at',starts),('finished_at',ends)]:
            try:
                stamp=datetime.fromisoformat(str(attempt.get(field,'')).replace('Z','+00:00'))
                if stamp.tzinfo: values.append(stamp)
            except ValueError: pass
    return {'schema_version':'cloud-execution-receipt-v1',
        'scheduler_event_time':target['scheduler_event_time'],'actual_start':target['actual_start'],
        'report_target_date':target['target_date'],'cutoff':target['coverage_end'],
        'coverage_start':target['coverage_start'],
        'actual_collection_start':min(starts).isoformat() if starts else 'UNKNOWN_NO_QUERY_CLOCK',
        'actual_collection_end':max(ends).isoformat() if ends else 'UNKNOWN_NO_QUERY_CLOCK',
        'source_attempt_count':len(attempts),
        'retrieval_mode':'NEW_BOUNDED_PUBLIC_SOURCE_RETRIEVAL_NOT_ORIGINAL_RUNNER_SNAPSHOT'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--event-created-at',required=True)
    parser.add_argument('--trigger',choices=('schedule','workflow_dispatch'),required=True)
    parser.add_argument('--target-date')
    parser.add_argument('--output-root',type=Path,required=True)
    parser.add_argument('--public-output',type=Path,required=True)
    args = parser.parse_args(argv)
    try:
        actual = datetime.now(timezone.utc).isoformat()
        target = resolve_target(args.event_created_at,actual,args.trigger,args.target_date)
        from lattice_digest.config import project_root
        from lattice_digest.public_contract import _reject_redirects
        root=args.output_root.absolute()
        _reject_redirects(root)
        if root.resolve() == project_root().resolve() or (root.exists() and any(root.iterdir())):
            fail('ARTIFACT_PATH_MISMATCH','cloud output must be an empty isolated root')
        # No env file, local canonical tree, mailbox or SMTP integration in cloud mode.
        from lattice_digest import run
        code=run.main(['--target-date',target['target_date'],'--since','36h','--output','markdown,json',
            '--send','none','--collector','github_actions','--quality-status','provisional','--run-mode','daily',
            '--output-root',str(root)],cloud_context=target)
        if code:
            return code
        from lattice_digest.report_gate import paths_for, safe_file, strict_json
        canonical_json,_=paths_for(root,'daily',target['target_date'])
        timing=execution_receipt(target,strict_json(safe_file(root,canonical_json))['metadata'])
        print(json.dumps({'event':'CLOUD_CANONICAL_GENERATED','execution':timing}))
        from lattice_digest.public_report import export
        export(root,'daily',target['target_date'],args.public_output)
        receipt=root/'audits'/'cloud-target.json'
        receipt.parent.mkdir(parents=True,exist_ok=True)
        receipt.write_bytes(encoded(target)+b'\n')
        (receipt.parent/'cloud-execution.json').write_bytes(encoded(timing)+b'\n')
        print(json.dumps({'gate':'PUBLIC_PRIVACY_GATE','status':'PASS','target_date':target['target_date'],
                          'publication':'CANDIDATE_ONLY_NO_REMOTE_WRITE'}))
        return 0
    except (GateError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'gate':'PUBLIC_PRIVACY_GATE' if isinstance(exc,GateError) and exc.code.startswith('PUBLIC_') else 'PRODUCTION_REPORT_GATE','status':'FAIL',
            'code':exc.code if isinstance(exc,GateError) else 'CLOUD_GENERATION_FAILED',
            'diagnostic':str(exc) if isinstance(exc,GateError) else 'details redacted'}))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
