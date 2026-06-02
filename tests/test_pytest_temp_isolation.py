from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_pyproject_uses_repo_local_pytest_basetemp() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    pytest_config = pyproject["tool"]["pytest"]["ini_options"]

    assert pytest_config["testpaths"] == ["tests"]
    assert "--basetemp=.pytest_tmp" in pytest_config["addopts"]
    assert ".pytest_tmp" in pytest_config["norecursedirs"]


def test_github_workflows_use_repo_local_pytest_basetemp() -> None:
    for workflow_path in [
        ".github/workflows/daily.yml",
        ".github/workflows/ci.yml",
    ]:
        workflow = _read(workflow_path)

        assert "python -m pytest tests --basetemp=.pytest_tmp" in workflow
        assert not re.search(r"(?m)^\s*(?:run:\s*)?python -m pytest\s*$", workflow)
        assert not re.search(r"(?m)^\s*(?:run:\s*)?pytest\s*$", workflow)


def test_manual_publish_uses_repo_local_temp_and_basetemp() -> None:
    bat = _read("scripts/manual_publish_to_github.bat")

    assert 'set "TEMP=%CD%\\.pytest_tmp"' in bat
    assert 'set "TMP=%CD%\\.pytest_tmp"' in bat
    assert 'if not exist ".pytest_tmp" mkdir ".pytest_tmp"' in bat
    assert "python -m pytest tests --basetemp=.pytest_tmp" in bat
    assert "git add ." not in bat.lower()
    assert "push --force" not in bat.lower()


def test_run_project_tests_helper_is_manual_and_repo_local() -> None:
    bat = _read("scripts/run_project_tests.bat")
    lowered = bat.lower()

    assert 'set "TEMP=%CD%\\.pytest_tmp"' in bat
    assert 'set "TMP=%CD%\\.pytest_tmp"' in bat
    assert "python -m pytest tests --basetemp=.pytest_tmp" in bat
    assert "git commit" not in lowered
    assert "git push" not in lowered
    assert "schtasks" not in lowered
    assert "cron" not in lowered


def test_no_scheduler_files_are_added_for_temp_isolation() -> None:
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
