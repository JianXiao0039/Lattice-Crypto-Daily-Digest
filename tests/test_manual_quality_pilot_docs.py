from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REAL_PILOT = ROOT / "docs" / "real-manual-quality-pilot.md"
PUBLISH_DOC = ROOT / "docs" / "manual-github-publish.md"
PUBLISH_BAT = ROOT / "scripts" / "manual_publish_to_github.bat"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_manual_quality_pilot_docs_and_helper_exist() -> None:
    assert REAL_PILOT.exists()
    assert PUBLISH_DOC.exists()
    assert PUBLISH_BAT.exists()


def test_readme_links_manual_quality_pilot_docs() -> None:
    readme = _read(ROOT / "README.md")

    assert "docs/real-manual-quality-pilot.md" in readme
    assert "docs/manual-github-publish.md" in readme
    assert "manual full-quality runs" in readme
    assert "low-load is optional fallback" in readme
    assert "No scheduled automation is configured" in readme


def test_docs_state_quality_first_manual_boundaries() -> None:
    combined = "\n".join([_read(REAL_PILOT), _read(PUBLISH_DOC)])

    assert "Manual-only usage" in combined
    assert "quality-first manual run" in combined
    assert "Low-load is fallback, not default for quality generation" in combined
    assert "No scheduled automation is configured" in combined
    assert "Windows Task Scheduler" in combined
    assert "cron" in combined
    assert "background service" in combined
    assert "startup task" in combined
    assert "No force push" in combined
    assert "Forbidden artifacts must not be committed" in combined


def test_docs_cover_quality_first_commands_and_fallback_modes() -> None:
    pilot = _read(REAL_PILOT)

    for command in [
        "python -m lattice_digest.workflow status",
        "python -m lattice_digest.workflow doctor",
        "python -m lattice_digest.workflow daily --execute",
        "python -m lattice_digest.workflow weekly --execute --generate-notes",
        "python -m lattice_digest.workflow full --execute --generate-notes",
    ]:
        assert command in pilot

    assert "When to use low-load" in pilot
    assert "When to use dry-run" in pilot
    assert "When to use no-network / offline" in pilot


def test_manual_publish_bat_avoids_unsafe_automation_and_git_patterns() -> None:
    bat = _read(PUBLISH_BAT).lower()

    assert "git add ." not in bat
    assert "push --force" not in bat
    assert "schtasks" not in bat
    assert "cron" not in bat
    assert "git push origin main" in bat
    assert "git pull --rebase origin main" in bat
    assert "python -m pytest tests" in bat
    assert "python scripts/check_release_hygiene.py" in bat
    assert "git diff --check" in bat
    assert "does not install any scheduled task" in bat


def test_manual_publish_bat_blocks_forbidden_artifacts() -> None:
    bat = _read(PUBLISH_BAT)

    for forbidden in [
        ".env",
        "papers.db",
        "state/reading-queue.json",
        "__pycache__",
        ".pytest_tmp",
        "exports/",
        "audits/",
        "data/",
        "digests/",
    ]:
        assert forbidden in bat

    assert "Forbidden staged artifact" in bat
