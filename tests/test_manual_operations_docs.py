from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "docs" / "manual-operations-runbook.md",
    ROOT / "docs" / "recovery-playbook.md",
    ROOT / "docs" / "artifact-retention-policy.md",
    ROOT / "docs" / "troubleshooting.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_manual_operations_docs_exist() -> None:
    for path in DOCS:
        assert path.exists(), f"missing manual operations doc: {path}"


def test_readme_links_manual_operations_docs() -> None:
    readme = _read(ROOT / "README.md")

    for relative in [
        "docs/manual-operations-runbook.md",
        "docs/recovery-playbook.md",
        "docs/artifact-retention-policy.md",
        "docs/troubleshooting.md",
    ]:
        assert relative in readme


def test_manual_operations_docs_state_no_scheduled_automation() -> None:
    combined = "\n".join(_read(path).lower() for path in DOCS)

    assert "no scheduled automation is configured" in combined
    assert "windows task scheduler" in combined
    assert "cron" in combined
    assert "background" in combined
    assert "auto-start" in combined or "startup task" in combined


def test_manual_operations_docs_cover_dry_run_low_load_and_offline_usage() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    assert "dry-run" in combined
    assert "dry-run default" in combined
    assert "--low-load" in combined
    assert "low-load mode" in combined
    assert "--no-network" in combined
    assert "--offline" in combined


def test_manual_operations_docs_distinguish_read_only_and_write_commands() -> None:
    runbook = _read(ROOT / "docs" / "manual-operations-runbook.md")

    assert "Read-only commands" in runbook
    assert "Commands that write files" in runbook
    assert "python -m lattice_digest.workflow status" in runbook
    assert "python -m lattice_digest.workflow doctor" in runbook
    assert "python -m lattice_digest.workflow weekly --execute --low-load" in runbook


def test_manual_operations_docs_cover_generated_artifacts_and_recovery() -> None:
    combined = "\n".join(_read(path) for path in DOCS)

    for text in [
        "Generated artifacts",
        "must not be committed",
        "state/reading-queue.json",
        "papers.db",
        ".pytest_tmp",
        "git clean -ndX",
        "reading queue",
        "Windows SQLite file lock",
        "ZoneInfo",
        "tzdata",
        "CI failure triage",
    ]:
        assert text in combined


def test_manual_operations_docs_do_not_contain_secret_patterns() -> None:
    combined = "\n".join([_read(ROOT / "README.md"), *(_read(path) for path in DOCS)])

    for forbidden in ["ghp_", "github_pat_", "sk-", "xoxb-", "AKIA"]:
        assert forbidden not in combined
