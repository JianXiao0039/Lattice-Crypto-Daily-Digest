from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "verify_daily_digest_git_tracking_2026_06_04_to_2026_06_10.py"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


def test_tracking_audit_distinguishes_tracked_digest_and_ignored_data(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / ".gitignore").write_text("digests/*.md\ndata/*.json\n", encoding="utf-8")
    (tmp_path / "digests").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "digests" / "2026-06-04.md").write_text("digest\n", encoding="utf-8")
    (tmp_path / "data" / "2026-06-04.json").write_text("{}\n", encoding="utf-8")
    _git(tmp_path, "add", ".gitignore")
    _git(tmp_path, "add", "-f", "digests/2026-06-04.md")
    _git(tmp_path, "commit", "-m", "add digest")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(tmp_path),
            "--remote-ref",
            "HEAD",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    first = payload["dates"][0]

    assert first["digest"]["local_exists"] is True
    assert first["digest"]["git_tracked"] is True
    assert first["digest"]["ignored_by_standard_check"] is False
    assert first["digest"]["matching_ignore_rule"] is not None
    assert first["digest"]["remote_present"] is True
    assert first["data"]["local_exists"] is True
    assert first["data"]["git_tracked"] is False
    assert first["data"]["matching_ignore_rule"] is not None
    assert first["data"]["remote_present"] is False
