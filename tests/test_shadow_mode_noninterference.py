from __future__ import annotations

import hashlib
import importlib.util
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_v0_5_shadow_mode_pilot.py"
SPEC = importlib.util.spec_from_file_location("v0_5_shadow_mode_noninterference", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _production_snapshot() -> dict[str, str]:
    snapshot: dict[str, str] = {}
    paths = [ROOT / "papers.db"]
    for directory in (ROOT / "data", ROOT / "digests", ROOT / "handoffs"):
        if directory.exists():
            paths.extend(path for path in directory.rglob("*") if path.is_file())
    for path in paths:
        if path.is_file():
            snapshot[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def test_manual_shadow_run_does_not_modify_production_artifacts() -> None:
    before = _production_snapshot()
    payload = MODULE.build_controlled_pilot(
        MODULE.load_json(MODULE.DEFAULT_INPUT),
        MODULE.load_json(MODULE.DEFAULT_RULES),
        run_id="noninterference-test",
    )
    shadow_root = ROOT / "audits/shadow"
    shadow_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=shadow_root) as directory:
        MODULE.write_outputs(
            payload,
            Path(directory) / "shadow",
            snapshot_path=MODULE.DEFAULT_INPUT,
            rules_path=MODULE.DEFAULT_RULES,
        )
    assert _production_snapshot() == before


def test_shadow_entrypoint_has_no_production_or_ars_runtime_imports() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        "from lattice_digest",
        "import lattice_digest",
        "academic_research_suite",
        "academic-research-suite",
        "subprocess",
    )
    assert not any(value in text for value in forbidden)
