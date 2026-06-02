from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _pytest_command_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if "python -m pytest" in line
    ]


def test_pyproject_limits_pytest_collection_to_project_tests() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    pytest_config = pyproject["tool"]["pytest"]["ini_options"]

    assert pytest_config["testpaths"] == ["tests"]

    norecursedirs = set(pytest_config["norecursedirs"])
    for dirname in [
        ".git",
        ".venv",
        "venv",
        "env",
        "build",
        "dist",
        "site-packages",
        "Lib",
        "Scripts",
        "exports",
        "audits",
        ".pytest_tmp",
        "__pycache__",
    ]:
        assert dirname in norecursedirs


def test_github_actions_use_project_scoped_pytest() -> None:
    for workflow_path in [
        ".github/workflows/daily.yml",
        ".github/workflows/ci.yml",
    ]:
        workflow = _read(workflow_path)
        lines = _pytest_command_lines(workflow)

        assert lines
        assert all("python -m pytest tests" in line for line in lines)
        assert not re.search(r"(?m)^\s*(?:run:\s*)?python -m pytest\s*$", workflow)


def test_manual_publish_uses_project_scoped_pytest() -> None:
    bat = _read("scripts/manual_publish_to_github.bat")
    lines = _pytest_command_lines(bat)

    assert lines == ["python -m pytest tests"]
    assert not re.search(r"(?m)^\s*python -m pytest\s*$", bat)
    assert "git add ." not in bat.lower()
    assert "push --force" not in bat.lower()


def test_no_scheduler_files_are_added() -> None:
    forbidden_paths = [
        "watcher.ps1",
        "start_watcher.bat",
        "install_watcher_task.ps1",
        "uninstall_watcher_task.ps1",
        "scripts/watcher.ps1",
        "scripts/start_watcher.bat",
        "scripts/install_watcher_task.ps1",
        "scripts/uninstall_watcher_task.ps1",
    ]

    for relative_path in forbidden_paths:
        assert not (ROOT / relative_path).exists()
