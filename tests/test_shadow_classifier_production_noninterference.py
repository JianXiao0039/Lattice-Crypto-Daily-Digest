from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _digest_tree(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {
        file.relative_to(ROOT).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted(path.rglob("*"))
        if file.is_file()
    }


def test_phase_13d_scripts_are_not_imported_by_production_or_workflows() -> None:
    forbidden = ("adjudicate_v0_5_human_annotations", "run_v0_5_shadow_pilot")
    paths = list((ROOT / "src/lattice_digest").rglob("*.py"))
    paths += list((ROOT / ".github/workflows").glob("*.yml"))
    paths += list((ROOT / ".github/workflows").glob("*.yaml"))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not any(name in text for name in forbidden), path


def test_phase_13d_additions_do_not_modify_authoritative_artifacts(tmp_path: Path) -> None:
    before = {name: _digest_tree(ROOT / name) for name in ("data", "digests", "handoffs")}
    adjudicator = _load_module("phase_13d_adjudicator", ROOT / "scripts/adjudicate_v0_5_human_annotations.py")
    rows, errors = adjudicator.load_annotation_rows(adjudicator.DEFAULT_ANNOTATIONS)
    adjudicated = adjudicator.adjudicate(adjudicator._load_json(adjudicator.DEFAULT_SOURCE_PACK), rows, errors)
    adjudicator.write_outputs(adjudicated, tmp_path / "adjudicated")

    pilot = _load_module("phase_13d_pilot", ROOT / "scripts/run_v0_5_shadow_pilot.py")
    payload = pilot.run_pilot(
        pilot.SAMPLE.build_sample(ROOT),
        adjudicated,
        pilot._load_json(pilot.DEFAULT_RULES),
    )
    pilot.write_outputs(payload, tmp_path / "pilot")
    after = {name: _digest_tree(ROOT / name) for name in ("data", "digests", "handoffs")}
    assert after == before


def test_shadow_pilot_remains_outside_production_package() -> None:
    assert not (ROOT / "src/lattice_digest/shadow_track_classifier.py").exists()
    assert (ROOT / "scripts/run_v0_5_shadow_pilot.py").is_file()
