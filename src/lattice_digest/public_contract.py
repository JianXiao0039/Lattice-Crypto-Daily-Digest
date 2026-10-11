"""Shared public entry contract: live authority, imports and one artifact root."""
from __future__ import annotations
import importlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from lattice_digest.runtime_paths import RuntimePaths, env_file
from lattice_digest.runtime_provenance import runtime_provenance, public_runtime_allowed, schedule_telemetry


def _reject_redirects(path: Path) -> None:
    """Check the lexical route too: resolve() alone hides junctions/symlinks."""
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part, 'is_junction', lambda: False)():
            raise ValueError(f'public runtime path redirect is forbidden: {part}')


def validate_public_paths(paths: RuntimePaths) -> None:
    """Only the exact operations checkout may live under canonical data."""
    canonical = Path(os.environ['LATTICE_DIGEST_CANONICAL_ROOT']).expanduser().absolute()
    expected = canonical / '.ops' / 'runtime' / 'published'
    _reject_redirects(canonical)
    _reject_redirects(Path.cwd())
    _reject_redirects(Path(__file__).absolute())
    _reject_redirects(paths.code_root / '.git')
    if paths.code_root.is_relative_to(paths.canonical_root):
        _reject_redirects(expected)
        if paths.code_root != expected.resolve():
            raise ValueError('untrusted nested public runtime; expected .ops/runtime/published')
        if not (paths.code_root / '.git').is_dir():
            raise ValueError('nested runtime requires an independent Git clone')
    elif tuple(part.lower() for part in paths.code_root.parts[-3:]) == ('.ops', 'runtime', 'published'):
        raise ValueError('operations runtime does not belong to configured canonical root')
    for name in ('data_root', 'digest_root', 'audit_root', 'state_root', 'export_root', 'database_path'):
        target = getattr(paths, name)
        _reject_redirects(target)
        if not target.resolve().is_relative_to(paths.canonical_root):
            raise ValueError(f'canonical artifact path escape: {name}')
    # Published trees may retain historical data in Git, but execution checkouts
    # must omit it via sparse checkout rather than create a second data universe.
    for name in ('papers.db', 'data', 'digests', 'state', 'exports', 'audits'):
        target = paths.code_root / name
        if target.exists() or target.is_symlink():
            raise ValueError(f'runtime-local artifact universe is forbidden: {name}')
    for entry in os.environ.get('PYTHONPATH', '').split(os.pathsep) if 'PYTHONPATH' in os.environ else ():
        if not entry:
            raise ValueError('unexpected empty public runtime PYTHONPATH entry')
        path = Path(entry).absolute()
        _reject_redirects(path)
        if path.resolve() != paths.code_root / 'src':
            raise ValueError('unexpected public runtime PYTHONPATH entry')
    for entry in sys.path:
        path = Path(entry or Path.cwd()).absolute()
        _reject_redirects(path)
        resolved = path.resolve()
        if resolved.is_relative_to(paths.canonical_root) and resolved not in (
                paths.code_root, paths.code_root / 'src'):
            raise ValueError('canonical development root must not be a Python import path')


def trace_imports(paths: RuntimePaths, dependencies: list[str]) -> list[str]:
    """Load reviewed modules without calling discovery or artifact-producing functions."""
    for name in dependencies:
        if not name.endswith('.py'):
            continue
        module = name.removeprefix('src/').removesuffix('.py').replace('/', '.')
        module = module.removesuffix('.__init__')
        importlib.import_module(module)
    observed = []
    for name, module in list(sys.modules.items()):
        filename = getattr(module, '__file__', None)
        if (filename and paths.canonical_root != paths.code_root
                and Path(filename).resolve().is_relative_to(paths.canonical_root)
                and not Path(filename).resolve().is_relative_to(paths.code_root)):
            raise ValueError(f'Python code imported from canonical development tree: {name}')
        if filename:
            _reject_redirects(Path(filename).absolute())
        package_owned = name in ('lattice_digest', 'scripts') or name.startswith(('lattice_digest.', 'scripts.'))
        if not package_owned and not (filename and Path(filename).resolve().is_relative_to(paths.code_root)):
            continue
        if filename is None:
            # A namespace package must not search outside the published tree.
            for entry in getattr(module, '__path__', ()):
                _reject_redirects(Path(entry).absolute())
                if not Path(entry).resolve().is_relative_to(paths.code_root):
                    raise ValueError(f'public namespace outside published code root: {name}')
            continue
        path = Path(filename).resolve()
        if not path.is_relative_to(paths.code_root):
            raise ValueError(f'public import outside published code root: {name}')
        relative = path.relative_to(paths.code_root).as_posix()
        if relative not in dependencies:
            raise ValueError(f'import omitted from command manifest: {relative}')
        observed.append(relative)
    return sorted(set(observed))


def public_preflight(profile: str) -> tuple[RuntimePaths, dict]:
    if not os.environ.get('LATTICE_DIGEST_CANONICAL_ROOT'):
        raise ValueError('public runtime requires explicit LATTICE_DIGEST_CANONICAL_ROOT')
    if not Path(os.environ['LATTICE_DIGEST_CANONICAL_ROOT']).expanduser().is_absolute():
        raise ValueError('public canonical root must be absolute')
    paths = RuntimePaths.resolve()
    if not paths.canonical_root.is_dir() or paths.canonical_root == paths.code_root:
        raise ValueError('public canonical root must be an existing directory separate from code')
    if Path.cwd().resolve() != paths.code_root:
        raise ValueError('public automation CWD must be the published code root')
    validate_public_paths(paths)
    info = runtime_provenance(paths.code_root, profile, verify_remote=True)
    if not public_runtime_allowed(info, public_automation=True):
        raise ValueError('PUBLIC_AUTOMATION_RUNTIME_CODE_BLOCKED: ' + json.dumps(info))
    observed = trace_imports(paths, info['runtime_dependency_paths'])
    secret_file = env_file(paths.code_root, public=True)
    return paths, {'preflight': True, 'writes': 0, 'discovery': 'NOT_STARTED',
                   'runtime_paths': paths.as_dict(), 'runtime_provenance': info,
                   'observed_import_paths': observed,
                   'secret_configuration': {'source': 'EXPLICIT_ENV_FILE' if secret_file else 'PROCESS_ENVIRONMENT',
                                            'credential_presence': {name: bool(os.environ.get(name)) for name in
                                                ('SEMANTIC_SCHOLAR_API_KEY', 'CONTACT_EMAIL', 'OPENAI_API_KEY')}},
                   **schedule_telemetry(datetime.now(ZoneInfo('Asia/Singapore')))}


def finish_telemetry(paths: RuntimePaths, profile: str, started: datetime, provenance: dict) -> None:
    """Only executing workflows write a finish record; preflight never calls this."""
    metadata = {**provenance, **schedule_telemetry(started, datetime.now(ZoneInfo('Asia/Singapore'))),
                'runtime_paths': paths.as_dict(), 'command_profile': profile}
    target = paths.audit_root / 'runtime' / f"{started.strftime('%Y%m%dT%H%M%S%f')}-{profile}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
