"""Published Daily entry; no implicit development code or duplicate data tree."""
from __future__ import annotations
import json
import os
import sys
from lattice_digest.public_contract import public_preflight, record_entry_failure
from lattice_digest.workflow import doctor_report
from lattice_digest import run
from lattice_digest.period_delivery import writer_lock
from datetime import datetime
from zoneinfo import ZoneInfo


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    proof = {}; stage = 'PREFLIGHT'
    try:
        paths, proof = public_preflight('DAILY')
        code, doctor = doctor_report(strict=True)
        if code:
            raise ValueError('public workflow doctor failed: ' + json.dumps(doctor))
        args = run.parse_args(argv)
        if args.output_root is not None and args.output_root.resolve() != paths.canonical_root:
            raise ValueError('public Daily --output-root must match the single canonical root')
        if args.preflight:
            proof['doctor'] = doctor
        os.environ['LATTICE_DIGEST_PUBLIC_AUTOMATION'] = '1'
        stage = 'PIPELINE_ENTERED'
        if args.preflight or args.dry_run:
            return run.main(argv, preflight_proof=proof)
        key=str(args.target_date or args.date or datetime.now(ZoneInfo('Asia/Singapore')).date())
        with writer_lock(paths,'DAILY',key):
            return run.main(argv, preflight_proof=proof)
    except (OSError,ValueError) as exc:
        print(str(exc))
        receipt = record_entry_failure('DAILY', exc, stage=stage, proof=proof, arguments=argv)
        if receipt: print('Operational failure receipt: ' + receipt)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
