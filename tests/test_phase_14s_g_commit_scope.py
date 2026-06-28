from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "fixtures" / "phase14s" / "phase-14s-g-proposed-commit-manifest.json"


def _included_paths() -> set[str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {entry["path"] for entry in data["files"] if entry["included"]}


def test_commit_scope_excludes_reports_manifests_and_generated_artifacts() -> None:
    included = _included_paths()
    assert not any(path.startswith("docs/reports/") for path in included)
    assert not any(path.startswith("docs/reports_incoming/") for path in included)
    assert not any(path.startswith("docs/reports/_incoming/") for path in included)
    assert not any(path.startswith("audits/") for path in included)
    assert not any(path.startswith("data/") for path in included)
    assert not any(path.startswith("digests/") for path in included)


def test_commit_scope_includes_policy_tests_and_active_docs() -> None:
    included = _included_paths()
    assert "tests/test_phase_14s_a_default_switch.py" in included
    assert "tests/test_phase_14s_a_explicit_compatibility.py" in included
    assert "tests/test_phase_14s_a_invalid_environment_value.py" in included
    assert "tests/test_phase_14s_a_writers_remain_canonical.py" in included
    assert "README.md" in included
    assert "docs/manual-operations-runbook.md" in included


def test_commit_scope_has_no_git_write_or_automation_contract() -> None:
    included = _included_paths()
    for path in included:
        if path.startswith("tests/") or not path.endswith((".py", ".ps1", ".md")):
            continue
        text = (ROOT / path).read_text(encoding="utf-8", errors="replace")
        assert "git add ." not in text
        assert "git add -A" not in text
        assert "schtasks" not in text.lower()
        assert "Register-ScheduledTask" not in text
