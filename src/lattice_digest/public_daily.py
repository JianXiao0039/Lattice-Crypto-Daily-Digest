"""Published Daily entry; no implicit development code or duplicate data tree."""
from __future__ import annotations
import json
import os
import sys
from lattice_digest.public_contract import public_preflight
from lattice_digest.workflow import doctor_report
from lattice_digest import run


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
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
        return run.main(argv, preflight_proof=proof)
    except ValueError as exc:
        print(str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
