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


def _load_email_script():
    spec = importlib.util.spec_from_file_location("send_latest_digest_email", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_send_email_missing_smtp_config_fails_without_leaking_password() -> None:
    module = _load_email_script()
    saved = {name: os.environ.get(name) for name in module.REQUIRED_ENV}
    try:
        for name in module.REQUIRED_ENV:
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
    assert "17 1 * * *" in workflow
    assert "SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}" in workflow
    assert "your_smtp_app_password" not in workflow
    assert "super-secret-password" not in workflow

