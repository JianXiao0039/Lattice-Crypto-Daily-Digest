"""Read-only eligibility preview. Never exports or publishes historical reports."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from lattice_digest.report_gate import GateError, verify
from lattice_digest.public_report import project


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--period',action='append',required=True,help='Explicit bounded preview period; repeat for a reviewed selection')
    args=parser.parse_args(argv)
    eligible=[];blocked=[]
    for kind in ('daily','weekly','monthly'):
        for path in sorted((args.root/'data').glob('*/'+kind+'/*.json')):
            period=path.stem
            if period not in args.period:
                continue
            try:
                pair=verify(args.root,kind,period)
                public=project(pair)
                eligible.append({'report_type':kind,'report_period':period,
                    'public_generation_id':public['public_generation_id'],'quality':public['quality'],
                    'event_count':public['event_count'],'source_coverage_state':public['source_coverage_state'],
                    'preview_required':True,'publication_approved':False})
            except (ValueError,OSError,KeyError,TypeError) as exc:
                blocked.append({'report_type':kind,'report_period':period,
                    'code':exc.code if isinstance(exc,GateError) else 'UNASSESSED_INPUT'})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'schema_version':'public-eligibility-v1','eligible':eligible,
        'blocked':blocked,'publication':'NOT_ATTEMPTED'},ensure_ascii=False,indent=2),encoding='utf-8')
    return 0


if __name__=='__main__':raise SystemExit(main())
