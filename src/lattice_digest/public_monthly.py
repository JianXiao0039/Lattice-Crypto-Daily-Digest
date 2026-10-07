"""Public monthly synthesis and explicit opt-in canonical downstream steps."""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from lattice_digest.public_contract import public_preflight, finish_telemetry
from lattice_digest.monthly_synthesis import build_monthly_synthesis, write_monthly_outputs
from lattice_digest.runtime_provenance import schedule_telemetry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--month')
    parser.add_argument('--exports', action='store_true', help='Enable canonical queue, artifacts and progress.')
    parser.add_argument('--obsidian', action='store_true', help='Enable the separate Monthly Obsidian profile.')
    args = parser.parse_args(argv)
    if args.obsidian and not args.exports:
        parser.error('--obsidian requires --exports')
    started = datetime.now(ZoneInfo('Asia/Singapore'))
    profile = 'MONTHLY_OBSIDIAN' if args.obsidian else ('MONTHLY_EXPORTS' if args.exports else 'MONTHLY')
    try:
        paths, proof = public_preflight(profile)
        month = args.month or (started.date().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        first = datetime.strptime(month, '%Y-%m').date()
        following = first.replace(year=first.year + 1, month=1) if first.month == 12 else first.replace(month=first.month + 1)
        proof['period'] = {'month': month, 'from_date': first.isoformat(), 'to_date': (following - timedelta(days=1)).isoformat()}
        if args.preflight:
            print(json.dumps(proof, ensure_ascii=False, indent=2))
            return 0
        payload = build_monthly_synthesis(paths.data_root, month)
        payload.setdefault('metadata', {}).update(proof['runtime_provenance'])
        payload['metadata'].update(schedule_telemetry(started))
        payload['metadata']['runtime_paths'] = paths.as_dict()
        write_monthly_outputs(payload, paths.data_root, paths.digest_root)
        if args.exports:
            from lattice_digest.monthly_downstream import run_downstream
            run_downstream(paths, first.isoformat(), (following - timedelta(days=1)).isoformat(), obsidian=args.obsidian)
        finish_telemetry(paths, profile, started, proof['runtime_provenance'])
        return 0
    except ValueError as exc:
        print(str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
