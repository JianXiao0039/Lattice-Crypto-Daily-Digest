from __future__ import annotations

import contextlib
import importlib.util
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "send_latest_digest_email.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "daily.yml"
ENV_EXAMPLE_PATH = ROOT / ".env.example"


def _load_email_script():
    spec = importlib.util.spec_from_file_location("send_latest_digest_email", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_send_email_missing_smtp_config_fails_without_leaking_password() -> None:
    module = _load_email_script()
    env_names = set(module.REQUIRED_ENV) | set(module.LEGACY_ENV_ALIASES.values())
    saved = {name: os.environ.get(name) for name in env_names}
    try:
        for name in env_names:
            os.environ.pop(name, None)
        os.environ["SMTP_PASSWORD"] = "super-secret-password"

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = module.main()

        output = stderr.getvalue()
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    assert result == 1
    assert "missing SMTP configuration" in output
    assert "super-secret-password" not in output


def test_find_latest_digest_uses_latest_yyyy_mm_dd_file() -> None:
    module = _load_email_script()
    with TemporaryDirectory() as tmp:
        digests = Path(tmp)
        (digests / "2026-05-22.md").write_text("old", encoding="utf-8")
        (digests / "2026-05-24.md").write_text("new", encoding="utf-8")
        (digests / "notes.md").write_text("ignore", encoding="utf-8")

        latest = module.find_latest_digest(digests)

    assert latest is not None
    assert latest.name == "2026-05-24.md"


def test_daily_workflow_exists_and_uses_secret_for_smtp_password() -> None:
    assert WORKFLOW_PATH.exists()
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "name: Daily Lattice Crypto Digest" in workflow
    assert "workflow_dispatch:" in workflow
    assert "17 1 * * *" in workflow
    assert "contents: write" in workflow
    assert "concurrency:" in workflow
    assert "fetch-depth: 0" in workflow
    assert 'cache: "pip"' in workflow
    assert "SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}" in workflow
    assert "your_smtp_app_password" not in workflow
    assert "smtp.example.com" not in workflow
    assert "super-secret-password" not in workflow


def test_daily_workflow_verifies_generated_outputs() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "python -m pytest" in workflow
    assert "python -m lattice_digest.run --since 36h --output markdown,json --send none" in workflow
    assert 'markdown_path="digests/${digest_date}.md"' in workflow
    assert 'json_path="data/${digest_date}.json"' in workflow
    assert "test -f papers.db" in workflow
    assert "json.load(handle)" in workflow
    for section in [
        "今日核心结论",
        "高优先级论文",
        "AI4Lattice 与机器学习辅助密码分析",
        "格基约简与经典攻击",
        "PQC 标准、原语与实现",
        "阅读队列与精读建议",
        "可孵化研究 idea 与导师讨论问题",
        "数据源健康与空报告处理",
    ]:
        assert section in workflow


def test_daily_workflow_commit_scope_is_limited_to_digest_outputs() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "git add -- digests/*.md data/*.json papers.db" in workflow
    assert "git add ." not in workflow
    assert "git add -A" not in workflow
    assert "git add --all" not in workflow
    assert ".env" not in workflow
    assert "No digest changes to commit." in workflow
    assert 'git commit -m "daily lattice digest: ${digest_date}"' in workflow
    assert "git push origin main" in workflow


def test_daily_workflow_skips_email_when_smtp_secrets_are_missing() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "SMTP_HOST: ${{ secrets.SMTP_HOST }}" in workflow
    assert "SMTP_PORT: ${{ secrets.SMTP_PORT }}" in workflow
    assert "SMTP_USERNAME: ${{ secrets.SMTP_USERNAME }}" in workflow
    assert "SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}" in workflow
    assert "DIGEST_EMAIL_FROM: ${{ secrets.DIGEST_EMAIL_FROM }}" in workflow
    assert "DIGEST_EMAIL_TO: ${{ secrets.DIGEST_EMAIL_TO }}" in workflow
    assert 'if [ -n "$SMTP_HOST" ]' in workflow
    assert '&& [ -n "$SMTP_USERNAME" ]' in workflow
    assert '&& [ -n "$SMTP_PASSWORD" ]' in workflow
    assert '&& [ -n "$DIGEST_EMAIL_FROM" ]' in workflow
    assert '&& [ -n "$DIGEST_EMAIL_TO" ]' in workflow
    assert "python scripts/send_latest_digest_email.py" in workflow
    assert "Email sending skipped: SMTP secrets not configured." in workflow
    assert "exit 1" not in workflow


def test_email_script_accepts_github_secret_style_env_names() -> None:
    module = _load_email_script()
    env = {
        "SMTP_HOST": "smtp.test",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "digest@example.test",
        "SMTP_PASSWORD": "secret",
        "DIGEST_EMAIL_FROM": "digest@example.test",
        "DIGEST_EMAIL_TO": "reader@example.test",
    }

    assert module.missing_env(module.normalize_env(env)) == []


def test_email_script_accepts_legacy_local_env_aliases() -> None:
    module = _load_email_script()
    env = {
        "SMTP_HOST": "smtp.test",
        "SMTP_PORT": "587",
        "SMTP_USER": "digest@example.test",
        "SMTP_PASSWORD": "secret",
        "MAIL_FROM": "digest@example.test",
        "MAIL_TO": "reader@example.test",
    }

    normalized = module.normalize_env(env)

    assert normalized["SMTP_USERNAME"] == "digest@example.test"
    assert normalized["DIGEST_EMAIL_FROM"] == "digest@example.test"
    assert normalized["DIGEST_EMAIL_TO"] == "reader@example.test"
    assert module.missing_env(normalized) == []


def test_env_example_contains_only_placeholder_email_values() -> None:
    env_example = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    for line in [
        "SMTP_HOST=",
        "SMTP_PORT=",
        "SMTP_USERNAME=",
        "SMTP_PASSWORD=",
        "DIGEST_EMAIL_TO=",
        "DIGEST_EMAIL_FROM=",
    ]:
        assert line in env_example

    assert "your_smtp_app_password" not in env_example
    assert "super-secret-password" not in env_example
    assert "smtp.example.com" not in env_example
