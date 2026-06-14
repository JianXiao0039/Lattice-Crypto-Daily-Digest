from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAME = "run_v0_5_shadow_mode_pilot.py"


def test_shadow_mode_is_not_referenced_by_workflows_or_production_package() -> None:
    paths = list((ROOT / ".github/workflows").glob("*.yml"))
    paths += list((ROOT / ".github/workflows").glob("*.yaml"))
    paths += list((ROOT / "src/lattice_digest").rglob("*.py"))
    for path in paths:
        assert SCRIPT_NAME not in path.read_text(encoding="utf-8"), path


def test_shadow_mode_script_contains_no_scheduler_or_private_path_contract() -> None:
    text = (ROOT / "scripts" / SCRIPT_NAME).read_text(encoding="utf-8")
    forbidden = (
        "Task Scheduler",
        "schtasks",
        "cron",
        "PhD_Application",
        "ResearchArtifacts",
    )
    assert not any(value in text for value in forbidden)


def test_shadow_mode_is_not_a_runtime_dependency() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "academic-research-suite" not in pyproject
    assert "run_v0_5_shadow_mode_pilot" not in pyproject
