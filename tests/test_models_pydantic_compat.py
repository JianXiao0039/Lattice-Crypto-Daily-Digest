from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_models_import_without_pydantic_v2_deprecation_warning() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    code = """
import warnings
from pydantic.warnings import PydanticDeprecatedSince20
warnings.simplefilter("error", PydanticDeprecatedSince20)
from lattice_digest.models import make_paper_record, record_to_dict, copy_record
record = make_paper_record(title="LWE test", source="fixture", source_url="https://example.org")
record_to_dict(record)
copy_record(record)
"""
    result = subprocess.run([sys.executable, "-c", code], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    assert result.returncode == 0, result.stderr
