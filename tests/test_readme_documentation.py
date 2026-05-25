from __future__ import annotations

from pathlib import Path


README_PATH = Path(__file__).resolve().parents[1] / "README.md"


def _readme() -> str:
    return README_PATH.read_text(encoding="utf-8")


def test_readme_documents_daily_digest_outputs() -> None:
    readme = _readme()

    assert "## 项目功能" in readme
    assert "A/B/C/D" in readme
    assert "digests/YYYY-MM-DD.md" in readme
    assert "data/YYYY-MM-DD.json" in readme
    assert "papers.db" in readme


def test_readme_documents_github_actions_and_smtp_secrets() -> None:
    readme = _readme()

    assert "## 云端自动运行：GitHub Actions" in readme
    assert "01:17 UTC" in readme
    assert "09:17 Asia" in readme
    assert "Run workflow" in readme
    assert "自动提交" in readme
    assert "SMTP secrets" in readme
    for secret in [
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "DIGEST_EMAIL_TO",
        "DIGEST_EMAIL_FROM",
    ]:
        assert secret in readme
    assert "邮箱授权码或应用密码" in readme


def test_readme_documents_local_run_and_manual_bat_push() -> None:
    readme = _readme()

    assert "## 本地运行" in readme
    assert "python -m lattice_digest.run --since 36h --output markdown,json --send none" in readme
    assert "python -m pytest" in readme
    assert "## 本地手动补交到 GitHub" in readme
    assert "scripts\\push_all_digest_outputs.bat" in readme
    assert "不抓取论文" in readme
    assert "不运行分类" in readme
    assert "只提交 `digests/`、`data/` 和 `papers.db`" in readme
    assert "多个历史日期" in readme


def test_readme_discourages_watcher_and_explains_common_failures() -> None:
    readme = _readme()

    assert "## 不推荐 watcher 自启动" in readme
    assert "电脑持续开机" in readme
    assert "Codex sandbox" in readme
    assert "GitHub Actions 做云端每日定时运行" in readme
    assert "本地只保留 `scripts\\push_all_digest_outputs.bat`" in readme
    assert "## 常见问题" in readme
    assert "Node.js 20 warning" in readme
    assert "本地 push 失败" in readme
    assert "429 warning" in readme
    assert "不等于失败" in readme
    assert "本地 Codex 无法写 `.git`" in readme


def test_readme_does_not_require_creating_new_venv() -> None:
    readme = _readme().lower()

    assert "python -m venv" not in readme
    assert "virtualenv" not in readme
    assert "new .venv" not in readme
    assert "创建新的 .venv" not in readme
