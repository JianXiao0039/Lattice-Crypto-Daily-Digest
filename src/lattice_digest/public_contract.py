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
                and Path(filename).resolve().is_relative_to(paths.canonical_root)):
            raise ValueError(f'Python code imported from canonical development tree: {name}')
        if not (name == 'lattice_digest' or name.startswith(('lattice_digest.', 'scripts.'))):
            continue
        if filename is None:
            continue  # scripts can be a namespace package.
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
    if paths.canonical_root != paths.code_root:
        for entry in sys.path:
            if Path(entry or Path.cwd()).resolve().is_relative_to(paths.canonical_root):
                raise ValueError('canonical development root must not be a Python import path')
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
