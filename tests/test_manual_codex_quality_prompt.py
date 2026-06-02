from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_DOC = ROOT / "docs" / "manual-codex-quality-run-prompt.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_manual_codex_quality_prompt_exists_and_is_manual_only() -> None:
    assert PROMPT_DOC.exists()
    doc = _read(PROMPT_DOC)

    assert "manual-only" in doc.lower()
    assert "do not put it into a recurring automation" in doc.lower()
    assert "No scheduled automation is configured" in doc
    assert "Windows Task Scheduler" in doc
    assert "cron" in doc
    assert "startup task" in doc
    assert "background service" in doc
    assert "quality-first manual generation is allowed" in doc
    assert "Low-load / no-network / dry-run are fallback modes only" in doc


def test_manual_codex_quality_prompt_forbids_bare_pytest_and_recommends_safe_commands() -> None:
    doc = _read(PROMPT_DOC)

    assert "Never use bare `python -m pytest`" in doc
    assert "scripts\\run_project_tests.bat" in doc
    assert "python -m pytest tests --basetemp=.pytest_tmp" in doc
    assert "python -m lattice_digest.run --since 36h --output markdown,json --send none" in doc
    assert "旧的外部 Codex 自动化 prompt" in doc or "recurring ChatGPT / Codex automation" in doc


def test_manual_codex_quality_prompt_is_linked_from_docs_index_and_pilot() -> None:
    docs_index = _read(ROOT / "docs" / "index.md")
    pilot = _read(ROOT / "docs" / "real-manual-quality-pilot.md")

    assert "manual-codex-quality-run-prompt.md" in docs_index
    assert "manual-codex-quality-run-prompt.md" in pilot


def test_docs_and_scripts_do_not_recommend_bare_pytest_commands() -> None:
    search_paths = [ROOT / "README.md"]
    search_paths.extend((ROOT / "docs").rglob("*.md"))
    search_paths.extend((ROOT / "scripts").glob("*.bat"))
    search_paths.extend((ROOT / "scripts").glob("*.ps1"))
    search_paths.extend((ROOT / ".github" / "workflows").glob("*.yml"))

    bad_command = re.compile(r"(?m)^\s*(?:run:\s*)?python -m pytest\s*$")

    for path in search_paths:
        text = _read(path)
        assert not bad_command.search(text), path
        if "python -m pytest" in text:
            command_lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip().startswith("python -m pytest")
            ]
            for line in command_lines:
                assert line.startswith("python -m pytest tests"), f"{path}: {line}"
                assert "--basetemp=.pytest_tmp" in line, f"{path}: {line}"


def test_no_scheduled_automation_files_are_added_for_manual_codex_prompt() -> None:
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
