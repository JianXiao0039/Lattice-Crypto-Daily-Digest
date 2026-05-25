from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
README_PATH = ROOT / "README.md"


def test_no_project_watcher_or_startup_scripts_remain() -> None:
    forbidden_names = {
        "watcher.ps1",
        "start_watcher.bat",
        "install_watcher_task.ps1",
        "uninstall_watcher_task.ps1",
        "watch_digest_outputs_and_push.ps1",
    }

    existing_names = {path.name for path in SCRIPTS_DIR.glob("*") if path.is_file()}

    assert forbidden_names.isdisjoint(existing_names)


def test_scripts_do_not_register_windows_task_scheduler() -> None:
    forbidden_terms = [
        "schtasks",
        "register-scheduledtask",
        "new-scheduledtask",
        "task scheduler",
    ]

    for path in SCRIPTS_DIR.glob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for term in forbidden_terms:
            assert term not in text, f"{path.name} contains {term}"


def test_readme_recommends_actions_and_manual_bat_instead_of_watcher() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "不推荐 watcher 自启动" in readme
    assert "不推荐为本项目配置本地 watcher" in readme
    assert "Windows Task Scheduler" in readme
    assert "GitHub Actions" in readme
    assert "scripts\\push_all_digest_outputs.bat" in readme
    assert "手动补交" in readme
