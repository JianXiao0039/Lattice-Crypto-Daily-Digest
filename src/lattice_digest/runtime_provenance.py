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
from lattice_digest.remote_authority import live_remote, APPROVED_ORIGIN

ALLOWED_PUBLIC_STATES = {'PUBLISHED_CLEAN_RUNTIME', 'PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_WORKTREE'}


def runtime_provenance(root: Path, command: str = 'DAILY', *, verify_remote: bool = False) -> dict:
    result = {'runtime_git_head': None, 'runtime_origin_main': None,
              'runtime_code_manifest_sha256': None, 'runtime_code_state': 'UNKNOWN_RUNTIME_PROVENANCE',
              'runtime_dirty_runtime_paths': [], 'runtime_dirty_production_paths': [],
              'runtime_command_profile': command, 'runtime_dependency_paths': [],
              'runtime_provenance_observation': 'LIVE_REMOTE' if verify_remote else 'LOCAL_GIT_REFS_NO_FETCH',
              'runtime_python_executable': sys.executable,
              'runtime_package_directory': str(Path(__file__).resolve().parent)}
    result.update(authority_mode='AUTHORITY_UNVERIFIED', local_code_integrity='UNVERIFIED',
                  release_authorization='UNVERIFIED', remote_freshness='UNVERIFIED',
                  offline_approval='DISABLED_NO_PREEXISTING_AUTHENTICATED_TRUST_ROOT',
                  source_retrieval='NOT_ATTEMPTED', scientific_validation='NOT_RUN',
                  public_upload='NOT_ATTEMPTED')
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL, timeout=30)
    try:
        # Git discovery must not silently inherit the outer development repo.
        actual_root = Path(git('rev-parse', '--show-toplevel').decode().strip()).resolve()
        if actual_root != root.resolve():
            raise ValueError('runtime must have its own independent Git checkout')
        head = git('rev-parse', 'HEAD').decode().strip()
        origin = git('rev-parse', 'refs/remotes/origin/main').decode().strip()
        result.update(runtime_git_head=head)
        if verify_remote:
            # Integrity is evaluated against immutable HEAD blobs first. A local
            # tracking ref is never substituted for a failed live observation.
            origin = head
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
            result['local_code_integrity'] = 'FAILED'
            result['runtime_failure_category'] = 'LOCAL_RUNTIME_INTEGRITY_FAILURE'
            return result
        profile_paths(root, manifest, command)
        result['local_code_integrity'] = 'VERIFIED'
        if verify_remote:
            result['runtime_origin_main'] = None
            origin_url = git('remote', 'get-url', 'origin').decode().strip()
            if origin_url != APPROVED_ORIGIN:
                result.update(runtime_failure_category='REMOTE_ORIGIN_MISMATCH',
                              runtime_provenance_error='REMOTE_ORIGIN_MISMATCH')
                return result
            remote = live_remote(root, origin_url)
            result['remote_verification'] = remote
            if remote['status'] != 'VERIFIED':
                result.update(runtime_failure_category=remote['error_code'],
                              runtime_provenance_error=remote['error_code'])
                return result
            origin = remote['sha']
            result.update(runtime_origin_main=origin, remote_freshness='VERIFIED')
            if origin != head:
                result.update(runtime_code_state='UNPUBLISHED_RUNTIME_COMMIT',
                              runtime_failure_category='REMOTE_RUNTIME_SHA_MISMATCH')
                return result
            result.update(authority_mode='LIVE_REMOTE_VERIFIED', release_authorization='VERIFIED')
        dirty = bool(git('status', '--porcelain', '--untracked-files=normal'))
        result['runtime_code_state'] = 'PUBLISHED_RUNTIME_WITH_UNRELATED_DIRTY_WORKTREE' if dirty else 'PUBLISHED_CLEAN_RUNTIME'
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        # Git/config/parse failures can contain secret or remote-controlled text.
        detail = ('independent Git checkout required'
                  if str(exc) == 'runtime must have its own independent Git checkout'
                  else 'LOCAL_RUNTIME_CHECK_FAILED')
        result['runtime_provenance_error'] = type(exc).__name__ + ': ' + detail
        result['runtime_failure_category'] = 'LOCAL_RUNTIME_INTEGRITY_FAILURE'
    return result


def public_runtime_allowed(provenance: dict, *, public_automation: bool) -> bool:
    return not public_automation or (
        provenance.get('authority_mode') == 'LIVE_REMOTE_VERIFIED'
        and provenance['runtime_code_state'] in ALLOWED_PUBLIC_STATES)


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
