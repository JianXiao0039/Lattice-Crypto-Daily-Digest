"""Public weekly synthesis reads only canonical Daily inputs."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from lattice_digest.public_contract import public_preflight, finish_telemetry
from lattice_digest.weekly_synthesis import build_weekly_synthesis, write_weekly_outputs
from lattice_digest.runtime_provenance import schedule_telemetry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--from-date')
    parser.add_argument('--to-date')
    args = parser.parse_args(argv)
    started = datetime.now(ZoneInfo('Asia/Singapore'))
    try:
        paths, proof = public_preflight('WEEKLY')
        end = (datetime.fromisoformat(args.to_date).date() if args.to_date else
               started.date() - timedelta(days=started.weekday() + 1))
        start = datetime.fromisoformat(args.from_date).date() if args.from_date else end - timedelta(days=6)
        if start > end:
            raise ValueError('weekly start must not follow end')
        proof['period'] = {'from_date': start.isoformat(), 'to_date': end.isoformat()}
        if args.preflight:
            print(json.dumps(proof, ensure_ascii=False, indent=2))
            return 0
        payload = build_weekly_synthesis(paths.data_root, start, end)
        payload.setdefault('metadata', {}).update(proof['runtime_provenance'])
        payload['metadata'].update(schedule_telemetry(started))
        payload['metadata']['runtime_paths'] = paths.as_dict()
        write_weekly_outputs(payload, paths.data_root, paths.digest_root)
        finish_telemetry(paths, 'WEEKLY', started, proof['runtime_provenance'])
        return 0
    except ValueError as exc:
        print(str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
