"""Read-only identity of production code; output artifacts never make code dirty."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime
from typing import Mapping

PRODUCTION_PATHS = ('src/', 'config/', '.github/workflows/')
PRODUCTION_FILES = {'pyproject.toml', 'requirements.txt', 'requirements-dev.txt', 'uv.lock', 'poetry.lock',
                    'scripts/run_daily_digest.ps1', 'scripts/run_daily_digest_and_push.ps1',
                    'scripts/run_daily_digest_and_push.cmd', 'scripts/run_local_digest_backfill.ps1',
                    'scripts/run_local_digest_backfill.bat'}


def production_path(path: str) -> bool:
    return path.startswith(PRODUCTION_PATHS) or path in PRODUCTION_FILES


def runtime_provenance(root: Path) -> dict:
    result = {'runtime_git_head': None, 'runtime_origin_main': None,
              'runtime_code_manifest_sha256': None, 'runtime_code_state': 'UNKNOWN_RUNTIME_PROVENANCE',
              'runtime_dirty_production_paths': [], 'runtime_provenance_observation': 'LOCAL_GIT_REFS_NO_FETCH'}
    result['runtime_python_executable'] = sys.executable
    result['runtime_package_directory'] = str(Path(__file__).resolve().parent)
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL, timeout=10)
    try:
        head = git('rev-parse', 'HEAD').decode().strip()
        result['runtime_git_head'] = head
        origin = git('rev-parse', 'refs/remotes/origin/main').decode().strip()
        tracked = {p.decode() for p in git('ls-files', '-z').split(b'\0') if p}
        other = {p.decode() for p in git('ls-files', '-z', '--others', '--exclude-standard').split(b'\0') if p}
        dirty = {p.decode() for p in git('diff', '--name-only', '-z', 'HEAD').split(b'\0') if p} | other
        executable = sorted(p for p in tracked | other if production_path(p))
        manifest = {}
        for path in executable:
            target = root / path
            # LF normalization matches Git text checkout; opaque byte content remains hashed.
            manifest[path] = hashlib.sha256(target.read_bytes().replace(b'\r\n', b'\n')).hexdigest() if target.is_file() else 'MISSING'
        code_dirty = sorted(p for p in dirty if production_path(p))
        unpublished = sorted(p.decode() for p in git('diff', '--name-only', '-z', origin, head).split(b'\0')
                             if p and production_path(p.decode()))
        state = ('UNPUBLISHED_RUNTIME_CODE' if unpublished or code_dirty else
                 'PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_FILES' if dirty else 'PUBLISHED_CLEAN_RUNTIME')
        result.update(runtime_git_head=head, runtime_origin_main=origin, runtime_code_state=state,
                      runtime_dirty_production_paths=code_dirty,
                      runtime_unpublished_production_paths=unpublished,
                      runtime_code_manifest_sha256=hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest())
    except (OSError, subprocess.SubprocessError, UnicodeError):
        pass
    return result


def public_runtime_allowed(provenance: dict, *, public_automation: bool) -> bool:
    return not public_automation or provenance['runtime_code_state'] in {
        'PUBLISHED_CLEAN_RUNTIME', 'PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_FILES'}


def schedule_telemetry(started: datetime, finished: datetime | None = None,
                       environ: Mapping[str, str] | None = None) -> dict:
    env = os.environ if environ is None else environ
    scheduled = env.get('LATTICE_DIGEST_SCHEDULED_FOR', '')
    parsed = None
    try:
        parsed = datetime.fromisoformat(scheduled.replace('Z', '+00:00')) if scheduled else None
        if parsed is not None and parsed.tzinfo is None:
            parsed = None
    except ValueError:
        pass
    kind = env.get('LATTICE_DIGEST_TRIGGER_KIND', 'UNKNOWN').upper()
    if kind not in {'SCHEDULED', 'MANUAL', 'BACKFILL', 'RETRY'}:
        kind = 'UNKNOWN'
    return {'scheduled_for': parsed.isoformat() if parsed else 'UNKNOWN', 'trigger_kind': kind,
            'run_started_at': started.isoformat(), 'run_finished_at': finished.isoformat() if finished else 'UNKNOWN',
            'schedule_timezone': env.get('LATTICE_DIGEST_SCHEDULE_TIMEZONE') or 'UNKNOWN',
            'schedule_lag_seconds': (started - parsed).total_seconds() if parsed and started.tzinfo else 'UNKNOWN'}
