"""Import bridge for direct, uninstalled `python -m lattice_digest.run` usage."""

from __future__ import annotations

import pkgutil
from pathlib import Path

__path__ = pkgutil.extend_path(__path__, __name__)  # type: ignore[name-defined]
SRC_PACKAGE = Path(__file__).resolve().parents[1] / "src" / "lattice_digest"
if SRC_PACKAGE.exists():
    __path__.append(str(SRC_PACKAGE))  # type: ignore[name-defined]

__version__ = "0.1.0"

