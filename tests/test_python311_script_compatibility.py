from __future__ import annotations

import ast
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    ROOT / "scripts/evaluate_v0_5_track_precision.py",
    ROOT / "scripts/run_v0_5_shadow_pilot.py",
)


def test_shadow_evaluation_scripts_compile_on_supported_python() -> None:
    for script in SCRIPTS:
        py_compile.compile(str(script), doraise=True)


def test_shadow_evaluation_scripts_parse_with_python311_grammar() -> None:
    for script in SCRIPTS:
        source = script.read_text(encoding="utf-8")
        ast.parse(source, filename=str(script), feature_version=(3, 11))


def test_f_string_expressions_do_not_embed_markdown_escape_backslashes() -> None:
    incompatible_fragments = (".replace('|', '\\\\|')", '.replace("|", "\\\\|")')
    for script in SCRIPTS:
        for line in script.read_text(encoding="utf-8").splitlines():
            if "f\"" in line or "f'" in line:
                assert not any(fragment in line for fragment in incompatible_fragments), (script, line)
