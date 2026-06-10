from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "verify_v0_4_release_candidate.py"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


def test_release_candidate_verifier_reports_missing_required_artifacts(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path), "--remote-ref", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "all_daily_local: FAIL" in result.stdout
    assert "weekly_json_present: FAIL" in result.stdout
    assert "ci_status: TODO_VERIFY_EXTERNAL_CI" in result.stdout


def test_release_candidate_verifier_has_no_private_workspace_targets() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "PhD_Application" not in source
    assert "D:\\ResearchArtifacts" not in source
