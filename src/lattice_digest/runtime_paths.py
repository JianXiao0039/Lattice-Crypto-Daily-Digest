"""Published code and one explicit canonical artifact universe."""
from __future__ import annotations

from dataclasses import dataclass, asdict
import os
from pathlib import Path
from typing import Mapping

from lattice_digest.config import project_root


@dataclass(frozen=True)
class RuntimePaths:
    code_root: Path
    canonical_root: Path

    @classmethod
    def resolve(cls, *, code_root: Path | None = None, canonical_root: Path | None = None,
                environ: Mapping[str, str] | None = None) -> "RuntimePaths":
        env = os.environ if environ is None else environ
        code = (code_root or project_root()).expanduser().resolve()
        value = canonical_root or env.get("LATTICE_DIGEST_CANONICAL_ROOT") or code
        return cls(code, Path(value).expanduser().resolve())

    @property
    def data_root(self) -> Path:
        return self.canonical_root / "data"

    @property
    def digest_root(self) -> Path:
        return self.canonical_root / "digests"

    @property
    def audit_root(self) -> Path:
        return self.canonical_root / "audits"

    @property
    def state_root(self) -> Path:
        return self.canonical_root / "state"

    @property
    def export_root(self) -> Path:
        return self.canonical_root / "exports"

    @property
    def database_path(self) -> Path:
        return self.canonical_root / "papers.db"

    @property
    def config_root(self) -> Path:
        return self.code_root / "config"

    def as_dict(self) -> dict[str, str]:
        result = asdict(self)
        for name in ("data_root", "digest_root", "audit_root", "state_root", "export_root",
                     "database_path", "config_root"):
            result[name] = getattr(self, name)
        return {key: str(value) for key, value in result.items()}


def legacy_cli_root(name: str) -> Path:
    """Keep manual CWD-relative CLI defaults unless the root is explicit."""
    if os.environ.get("LATTICE_DIGEST_CANONICAL_ROOT"):
        return RuntimePaths.resolve().canonical_root / name
    return Path(name)


def env_file(code_root: Path, *, public: bool, environ: Mapping[str, str] | None = None) -> Path | None:
    env = os.environ if environ is None else environ
    explicit = env.get("LATTICE_DIGEST_ENV_FILE")
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_absolute() or not path.is_file():
            raise ValueError("LATTICE_DIGEST_ENV_FILE must name an existing absolute external file")
        return path.resolve()
    return None if public else code_root / ".env"
