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


def test_daily_workflow_has_no_mailbox_or_smtp_credentials() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "name: Daily Lattice Crypto Digest" in workflow
    assert "workflow_dispatch:" in workflow and "17 1 * * *" in workflow
    assert "cancel-in-progress: false" in workflow and "contents: read" in workflow
    assert "SMTP_" not in workflow and "DIGEST_EMAIL_" not in workflow and "GMAIL_" not in workflow


def test_daily_workflow_verifies_generated_outputs() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "python -m pytest tests/test_public_report_pipeline.py" in workflow
    assert "lattice_digest.cloud_daily" in workflow
    assert "from lattice_digest.report_gate import verify" in workflow
    assert "from lattice_digest.public_report import inspect_tree" in workflow
    assert "context['target_date']" in workflow
    assert "grep -q" not in workflow
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "ubuntu-latest" in ci and "windows-latest" in ci
    assert "python -m pytest tests --basetemp=.pytest_tmp" in ci


def test_daily_workflow_upload_scope_is_public_only() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "git add" not in workflow and "git commit" not in workflow and "git push" not in workflow
    assert "path: ${{ runner.temp }}/public-candidate/" in workflow
    assert "REMOTE_PUBLICATION_GATE CANDIDATE_READY" in workflow
    assert "needs: digest" in workflow and "lattice_digest.public_publisher" in workflow


def test_daily_cloud_does_not_send_email() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "send_latest_digest_email.py" not in workflow
    assert "secrets.SMTP" not in workflow
    assert "timeout-minutes: 35" in workflow


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
