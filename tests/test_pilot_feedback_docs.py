from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "docs" / "pilot-feedback-triage.md",
    ROOT / "docs" / "pilot-feedback-summary-template.md",
    ROOT / "docs" / "pilot-fix-prioritization.md",
]

REQUIRED_CATEGORIES = [
    "classification_false_positive",
    "classification_false_negative",
    "ranking_noise",
    "workflow_confusion",
    "slow_command",
    "artifact_clutter",
    "reading_queue_state",
    "obsidian_scaffold",
    "source_health_confusion",
    "windows_path_or_lock",
    "ci_only",
    "docs_gap",
    "release_hygiene",
    "wont_fix",
]

REQUIRED_PHASE_LABELS = [
    "Phase 9F: classifier calibration follow-up",
    "Phase 9G: workflow UX polish",
    "Phase 9H: artifact cleanup ergonomics",
    "Phase 9I: reading queue safety hardening",
    "Phase 9J: docs polish",
    "Phase 9K: release hardening",
    "wont_fix",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pilot_feedback_docs_exist() -> None:
    for path in DOCS:
        assert path.exists(), f"missing pilot feedback doc: {path}"


def test_readme_links_pilot_feedback_docs() -> None:
    readme = _read(ROOT / "README.md")

    for relative in [
        "docs/pilot-feedback-triage.md",
        "docs/pilot-feedback-summary-template.md",
        "docs/pilot-fix-prioritization.md",
    ]:
        assert relative in readme


def test_pilot_feedback_docs_cover_manual_only_and_no_scheduled_automation() -> None:
    combined = "\n".join(_read(path).lower() for path in DOCS)

    assert "manual-only usage" in combined
    assert "no scheduled automation is configured" in combined
    assert "windows task scheduler" in combined
    assert "cron" in combined
    assert "background daemon" in combined
    assert "startup task" in combined
    assert "automatic scheduled run" in combined


def test_pilot_feedback_docs_cover_safety_boundaries() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    assert "dry-run safety" in combined
    assert "low-load mode" in combined
    assert "no-network behavior" in combined
    assert "Generated artifacts must not be committed" in combined
    assert "generated artifacts must not be committed" in combined
    assert "Reading queue manual statuses should be preserved" in combined
    assert "reading queue manual statuses should be preserved" in combined


def test_pilot_feedback_docs_include_required_issue_categories() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for category in REQUIRED_CATEGORIES:
        assert category in combined


def test_pilot_feedback_docs_include_required_phase_target_labels() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for label in REQUIRED_PHASE_LABELS:
        assert label in combined

