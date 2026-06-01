from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PILOT_DOCS = [
    ROOT / "docs" / "one-week-manual-pilot.md",
    ROOT / "docs" / "pilot-acceptance-checklist.md",
    ROOT / "docs" / "pilot-issue-log-template.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pilot_docs_exist() -> None:
    for path in PILOT_DOCS:
        assert path.exists(), f"missing pilot doc: {path}"


def test_readme_links_pilot_docs() -> None:
    readme = _read(ROOT / "README.md")

    for relative in [
        "docs/one-week-manual-pilot.md",
        "docs/pilot-acceptance-checklist.md",
        "docs/pilot-issue-log-template.md",
    ]:
        assert relative in readme


def test_pilot_docs_state_manual_only_and_no_scheduled_automation() -> None:
    combined = "\n".join(_read(path).lower() for path in PILOT_DOCS)

    assert "manual-only usage" in combined
    assert "no scheduled automation is configured" in combined
    assert "windows task scheduler" in combined
    assert "cron" in combined
    assert "background" in combined
    assert "startup task" in combined
    assert "automatic scheduled run" in combined


def test_pilot_docs_cover_dry_run_low_load_and_no_network() -> None:
    combined = "\n".join(_read(path) for path in PILOT_DOCS)

    assert "dry-run default" in combined
    assert "--low-load" in combined
    assert "low-load mode" in combined
    assert "--no-network" in combined
    assert "--offline" in combined
    assert "no-network" in combined
    assert "offline usage" in combined


def test_pilot_docs_cover_artifact_and_reading_queue_boundaries() -> None:
    combined = "\n".join(_read(path) for path in PILOT_DOCS)

    assert "generated artifacts must not be committed" in combined
    assert "reading queue manual statuses should be preserved" in combined
    assert "git status does not show forbidden artifacts staged" in combined


def test_pilot_issue_log_has_required_fields_and_categories() -> None:
    issue_log = _read(ROOT / "docs" / "pilot-issue-log-template.md")

    for category in [
        "false positive classification",
        "missing important paper",
        "noisy ranking explanation",
        "confusing workflow output",
        "slow command",
        "generated artifact clutter",
        "reading queue status problem",
        "Obsidian scaffold problem",
        "source health confusion",
        "Windows path issue",
        "SQLite file lock issue",
        "CI-only issue",
        "documentation gap",
    ]:
        assert category in issue_log

    for field in [
        "Date:",
        "Command run:",
        "Expected behavior:",
        "Actual behavior:",
        "Severity: low / medium / high",
        "Reproduction steps:",
        "Suspected cause:",
        "Proposed fix:",
        "Phase target:",
        "Status: open / triaged / fixed / won't fix",
    ]:
        assert field in issue_log
