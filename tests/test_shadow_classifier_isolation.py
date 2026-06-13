from __future__ import annotations

from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parents[1]


def _text_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file() and path.suffix in {".py", ".yml", ".yaml"}]


def test_production_code_and_workflows_do_not_reference_shadow_classifier() -> None:
    forbidden = ("run_v0_5_shadow_track_classifier", "v0_5_shadow_track_rules")
    paths = _text_files(ROOT / "src" / "lattice_digest") + _text_files(ROOT / ".github" / "workflows")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not any(name in text for name in forbidden), path


def test_academic_research_suite_is_not_a_runtime_dependency() -> None:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = payload.get("project", {}).get("dependencies", [])
    optional = payload.get("project", {}).get("optional-dependencies", {})
    flattened = [str(item).lower() for item in dependencies]
    flattened.extend(str(item).lower() for values in optional.values() for item in values)
    assert not any("academic-research" in item for item in flattened)


def test_rules_are_explicitly_non_production() -> None:
    import json

    rules = json.loads((ROOT / "experiments" / "v0_5_shadow_track_rules.json").read_text(encoding="utf-8"))
    assert rules["experimental_only"] is True
    assert rules["production_consumption_allowed"] is False
