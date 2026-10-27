"""Public weekly synthesis reads only canonical Daily inputs."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from lattice_digest.public_contract import public_preflight, finish_telemetry, record_entry_failure
from lattice_digest.weekly_synthesis import build_weekly_synthesis, write_weekly_outputs
from lattice_digest.runtime_provenance import schedule_telemetry
from lattice_digest.period_delivery import writer_lock, publish_period


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--from-date')
    parser.add_argument('--to-date')
    args = parser.parse_args(argv)
    started = datetime.now(ZoneInfo('Asia/Singapore'))
    proof = {}; stage = 'PREFLIGHT'
    try:
        paths, proof = public_preflight('WEEKLY')
        end = (datetime.fromisoformat(args.to_date).date() if args.to_date else
               started.date() - timedelta(days=started.weekday() + 1))
        start = datetime.fromisoformat(args.from_date).date() if args.from_date else end - timedelta(days=6)
        if start.weekday()!=0 or end!=start+timedelta(days=6) or end>=started.date():
            raise ValueError('weekly production requires a completed Monday-Sunday ISO week')
        proof['period'] = {'from_date': start.isoformat(), 'to_date': end.isoformat()}
        if args.preflight:
            print(json.dumps(proof, ensure_ascii=False, indent=2))
            return 0
        stage = 'REPORT_GENERATION'
        key=f'{start.isocalendar().year}-W{start.isocalendar().week:02d}'
        with writer_lock(paths,'WEEKLY',key):
            payload = build_weekly_synthesis(paths.data_root, start, end)
            payload.setdefault('metadata', {}).update(proof['runtime_provenance'])
            payload['metadata'].update(schedule_telemetry(started))
            payload['metadata']['runtime_paths'] = paths.as_dict()
            publish_period(payload,paths,write_weekly_outputs)
        finish_telemetry(paths, 'WEEKLY', started, proof['runtime_provenance'])
        from lattice_digest.delivery_receipt import validate_generated
        receipt = validate_generated(paths.canonical_root, 'weekly', key)
        return 0 if receipt['scientific_validation_verified'] else 2
    except (OSError,ValueError) as exc:
        print(str(exc))
        receipt = record_entry_failure('WEEKLY', exc, stage=stage, proof=proof, arguments=argv)
        if receipt: print('Operational failure receipt: ' + receipt)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
