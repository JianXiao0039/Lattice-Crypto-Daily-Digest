from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_version_metadata_contains_current_release() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    init = _read("src/lattice_digest/__init__.py")

    assert pyproject["project"]["version"] == "0.4.1"
    assert '__version__ = "0.4.1"' in init


def test_changelog_documents_v010_capabilities_and_limits() -> None:
    changelog = _read("CHANGELOG.md")

    for text in [
        "v0.1.0",
        "Source Health",
        "authoritative backfill",
        "Weekly Research Brief",
        "Obsidian",
        "Known limitations",
        "Semantic Scholar works best with API key",
    ]:
        assert text in changelog


def test_release_note_documents_deployment_and_api_guidance() -> None:
    release_note = _read("docs/releases/v0.1.0.md")

    for text in [
        "v0.1.0",
        "local authoritative backfill",
        "Semantic Scholar",
        "Semantic Scholar: recommended API key",
        "Known limitations",
        "v0.2.0",
    ]:
        assert text.lower() in release_note.lower()


def test_release_checklist_contains_required_release_steps() -> None:
    checklist = _read("docs/release-checklist.md")

    for text in [
        "git tag -a v0.1.0",
        "python -m pytest",
        "no secrets",
        "no generated artifacts",
        "GitHub Release body template",
    ]:
        assert text in checklist


def test_readme_links_release_docs() -> None:
    readme = _read("README.md")

    assert "CHANGELOG.md" in readme
    assert "docs/releases/v0.4.1.md" in readme
    assert "docs/releases/v0.3.3.md" in readme
    assert "docs/index.md" in readme
    assert "docs/release-checklist.md" in readme
    assert "v0.4.1" in readme
    assert re.search(r"local (authoritative )?backfill", readme, flags=re.IGNORECASE)
