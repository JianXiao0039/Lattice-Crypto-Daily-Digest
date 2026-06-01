from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_INDEX = ROOT / "docs" / "index.md"
README = ROOT / "README.md"
CORE_DOCS = [
    DOC_INDEX,
    ROOT / "docs" / "manual-operations-runbook.md",
    ROOT / "docs" / "workflow-command-center.md",
    ROOT / "docs" / "manual-low-load-workflow.md",
    ROOT / "docs" / "recovery-playbook.md",
    ROOT / "docs" / "artifact-retention-policy.md",
    ROOT / "docs" / "troubleshooting.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_docs_index_exists() -> None:
    assert DOC_INDEX.exists()


def test_readme_links_docs_index_and_safe_quickstart() -> None:
    readme = _read(README)
    readme_lower = readme.lower()

    assert "docs/index.md" in readme
    assert "safe manual quickstart" in readme_lower
    assert "manual-only usage" in readme_lower
    assert "dry-run default" in readme_lower
    assert "low-load" in readme_lower
    assert "no-network" in readme_lower or "offline" in readme_lower
    assert "no scheduled automation is configured" in readme_lower


def test_docs_index_links_core_docs() -> None:
    index = _read(DOC_INDEX)

    for relative in [
        "manual-operations-runbook.md",
        "workflow-command-center.md",
        "manual-low-load-workflow.md",
        "recovery-playbook.md",
        "artifact-retention-policy.md",
        "troubleshooting.md",
        "one-week-manual-pilot.md",
        "pilot-acceptance-checklist.md",
        "pilot-issue-log-template.md",
        "pilot-feedback-triage.md",
        "pilot-feedback-summary-template.md",
        "pilot-fix-prioritization.md",
        "release-checklist.md",
        "releases/v0.3.1.md",
        "releases/v0.3.0.md",
        "releases/v0.2.0.md",
    ]:
        assert relative in index


def test_command_safety_matrix_exists() -> None:
    runbook = _read(ROOT / "docs" / "manual-operations-runbook.md")

    assert "Command safety matrix" in runbook
    for heading in [
        "Command",
        "Read-only or not",
        "Writes files or not",
        "Network behavior",
        "Low-load support",
        "Notes",
    ]:
        assert heading in runbook


def test_docs_cover_artifacts_and_reading_queue_state() -> None:
    combined = "\n".join(_read(path) for path in [README, *CORE_DOCS])
    combined_lower = combined.lower()

    assert "generated artifacts must not be committed" in combined_lower
    assert "reading queue manual statuses" in combined_lower
    assert "local state" in combined_lower
    assert "state/reading-queue.json" in combined


def test_docs_do_not_recommend_local_scheduled_automation() -> None:
    combined = "\n".join(_read(path).lower() for path in [README, *CORE_DOCS])

    forbidden_recommendations = [
        "scheduled automation as next step",
        "task scheduler as recommended next step",
        "task scheduler is recommended",
        "recommend task scheduler",
        "recommended task scheduler",
        "cron is recommended",
        "recommend cron",
        "recommended cron",
        "background service is recommended",
        "recommend background service",
        "startup task is recommended",
        "recommend startup task",
        "automatic scheduling is recommended",
        "recommend automatic scheduling",
    ]
    for phrase in forbidden_recommendations:
        assert phrase not in combined

    assert "no scheduled automation is configured" in combined
    assert "do not add windows task scheduler" in combined
    assert "cron" in combined
    assert "background services" in combined or "background service" in combined
    assert "startup task" in combined
    assert "automatic scheduling" in combined or "automatic scheduled" in combined

