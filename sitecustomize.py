"""Make the src layout importable for direct `python -m lattice_digest.run` use."""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if SRC.exists():
    src_text = str(SRC)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)

