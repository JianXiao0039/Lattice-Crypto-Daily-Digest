"""Read-only command-scoped published code authority; no bypass state."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime
from typing import Mapping
from lattice_digest.runtime_dependencies import MANIFEST_PATH, profile_paths, safe_path

ALLOWED_PUBLIC_STATES = {'PUBLISHED_CLEAN_RUNTIME', 'PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_WORKTREE'}


def runtime_provenance(root: Path, command: str = 'DAILY', *, verify_remote: bool = False) -> dict:
    result = {'runtime_git_head': None, 'runtime_origin_main': None,
              'runtime_code_manifest_sha256': None, 'runtime_code_state': 'UNKNOWN_RUNTIME_PROVENANCE',
              'runtime_dirty_runtime_paths': [], 'runtime_dirty_production_paths': [],
              'runtime_command_profile': command, 'runtime_dependency_paths': [],
              'runtime_provenance_observation': 'LIVE_REMOTE' if verify_remote else 'LOCAL_GIT_REFS_NO_FETCH',
              'runtime_python_executable': sys.executable,
              'runtime_package_directory': str(Path(__file__).resolve().parent)}
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL, timeout=30)
    try:
        head = git('rev-parse', 'HEAD').decode().strip()
        origin = git('rev-parse', 'refs/remotes/origin/main').decode().strip()
        if verify_remote:
            lines = git('ls-remote', '--heads', 'origin', 'refs/heads/main').decode().splitlines()
            if len(lines) != 1 or len(lines[0].split()) != 2:
                raise ValueError('remote main is unresolved')
            origin = lines[0].split()[0]
        result.update(runtime_git_head=head, runtime_origin_main=origin)
        if head != origin:
            result['runtime_code_state'] = 'UNPUBLISHED_RUNTIME_COMMIT'
            result['runtime_unpublished_production_paths'] = git('diff', '--name-only', origin, head).decode().splitlines()
            return result
        manifest = json.loads(git('show', f'{origin}:{MANIFEST_PATH}'))
        declared = manifest['profiles'][command]['paths']
        declared = [safe_path(path) for path in declared]
        request = ''.join(f'{origin}:{path}\n' for path in declared).encode()
        response = subprocess.run(['git', 'cat-file', '--batch'], cwd=root, input=request,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True, timeout=30).stdout
        blobs, offset = {}, 0
        for path in declared:
            boundary = response.index(b'\n', offset)
            header = response[offset:boundary].split()
            if len(header) != 3 or header[1] != b'blob':
                raise ValueError('published dependency blob is missing')
            size = int(header[2])
            offset = boundary + 1
            blobs[path] = response[offset:offset + size].replace(b'\r\n', b'\n')
            offset += size + 1
        hashes, changed = {}, []
        for path in declared:
            path = safe_path(path)
            target = root / path
            external = target.exists() and not target.resolve().is_relative_to(root.resolve())
            actual = target.read_bytes().replace(b'\r\n', b'\n') if target.is_file() and not external else None
            published = blobs[path]
            if actual != published or external:
                changed.append(path)
            hashes[path] = hashlib.sha256(actual).hexdigest() if actual is not None else 'MISSING'
        staged = git('diff', '--cached', '--name-only', '-z', 'HEAD').split(b'\0')
        changed.extend(p.decode() for p in staged if p and p.decode() in declared)
        code_dirty = sorted(set(changed))
        result.update(runtime_dirty_runtime_paths=code_dirty, runtime_dirty_production_paths=code_dirty,
                      runtime_dependency_paths=sorted(declared),
                      runtime_code_manifest_sha256=hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest())
        if code_dirty:
            result['runtime_code_state'] = 'DIRTY_RUNTIME_DEPENDENCY'
            return result
        profile_paths(root, manifest, command)
        dirty = bool(git('status', '--porcelain', '--untracked-files=normal'))
        result['runtime_code_state'] = 'PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_WORKTREE' if dirty else 'PUBLISHED_CLEAN_RUNTIME'
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        result['runtime_provenance_error'] = type(exc).__name__ + ': ' + str(exc)
    return result


def public_runtime_allowed(provenance: dict, *, public_automation: bool) -> bool:
    return not public_automation or provenance['runtime_code_state'] in ALLOWED_PUBLIC_STATES


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
    if kind not in {'SCHEDULED', 'MANUAL', 'BACKFILL', 'RECOVERY', 'RETRY'}:
        kind = 'UNKNOWN'
    return {'scheduled_for': parsed.isoformat() if parsed else 'UNKNOWN', 'trigger_kind': kind,
            'run_started_at': started.isoformat(), 'run_finished_at': finished.isoformat() if finished else 'UNKNOWN',
            'schedule_timezone': env.get('LATTICE_DIGEST_SCHEDULE_TIMEZONE') or 'UNKNOWN',
            'schedule_lag_seconds': (started - parsed).total_seconds() if parsed and started.tzinfo else 'UNKNOWN'}
