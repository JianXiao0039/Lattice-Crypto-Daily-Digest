from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_v0_4_1_release_candidate.py"
SPEC = importlib.util.spec_from_file_location("verify_v041", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_active_version_sources_are_v041() -> None:
    versions = MODULE.read_versions(ROOT)

    assert versions == {
        "pyproject": "0.4.1",
        "source_package": "0.4.1",
        "bridge_package": "0.4.1",
    }


def test_submission_contract_is_narrow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "daily.yml").read_text(encoding="utf-8")

    assert MODULE.validate_submission_contract(workflow) == []


def test_release_report_blocks_staged_files(monkeypatch) -> None:
    def fake_git(*args: str) -> str:
        if args == ("diff", "--cached", "--name-only"):
            return "papers.db"
        if args == ("rev-parse", "v0.4.0"):
            return MODULE.HISTORICAL_TARGET
        raise AssertionError(args)

    report = MODULE.build_report(ROOT, git=fake_git)

    assert report["local_release_checks_passed"] is False
    staging = next(item for item in report["checks"] if item["name"] == "release staging gate")
    assert staging["ok"] is False


def test_release_report_preserves_historical_tag(monkeypatch) -> None:
    def fake_git(*args: str) -> str:
        if args == ("diff", "--cached", "--name-only"):
            return ""
        if args == ("rev-parse", "v0.4.0"):
            return MODULE.HISTORICAL_TARGET
        raise AssertionError(args)

    report = MODULE.build_report(ROOT, git=fake_git)
    tag = next(item for item in report["checks"] if item["name"] == "historical tag immutable")

    assert tag["ok"] is True
    assert report["tag_decision"] == "blocked_by_multiple_conditions"
    assert report["external_gates"]["durable_post_tag_daily_run"] == "missing"
