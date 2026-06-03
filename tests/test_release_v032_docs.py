from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA")


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_v032_release_artifacts_are_archival_docs() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    src_init = _read("src/lattice_digest/__init__.py")
    bridge_path = ROOT / "lattice_digest" / "__init__.py"

    assert pyproject["project"]["version"] != "0.3.2"
    assert '__version__ = "0.3.2"' not in src_init
    if bridge_path.exists():
        assert '__version__ = "0.3.2"' not in bridge_path.read_text(encoding="utf-8")


def test_v032_release_doc_and_changelog_exist() -> None:
    assert (ROOT / "docs" / "releases" / "v0.3.2.md").exists()
    assert "v0.3.2" in _read("CHANGELOG.md")


def test_readme_links_v032_release_and_docs_index() -> None:
    readme = _read("README.md")

    assert "docs/releases/v0.3.2.md" in readme
    assert "docs/index.md" in readme
    assert "manual-only usage" in readme
    assert "dry-run default" in readme
    assert "--low-load" in readme
    assert "--no-network" in readme or "--offline" in readme
    assert "No scheduled automation is configured" in readme


def test_v032_release_notes_state_manual_safety_boundaries() -> None:
    release_doc = _read("docs/releases/v0.3.2.md")
    release_lower = release_doc.lower()

    for needle in [
        "manual-only usage",
        "dry-run default",
        "low-load mode",
        "no-network/offline usage",
        "no scheduled automation is added",
        "windows task scheduler",
        "cron job",
        "background service",
        "startup task",
        "automatic scheduled local run",
    ]:
        assert needle in release_lower


def test_v032_changelog_mentions_expected_release_scope() -> None:
    changelog = _read("CHANGELOG.md")

    for needle in [
        "v0.3.2",
        "Documentation polish",
        "docs/index.md",
        "safe manual quickstart",
        "Command safety matrix",
        "One-week manual pilot docs",
        "Pilot feedback triage docs",
        "Maintenance cleanup / warning reduction",
        "manual-only",
        "dry-run default",
        "Low-load mode",
        "No-network/offline usage",
        "No scheduled automation is added",
    ]:
        assert needle in changelog


def test_v032_release_docs_do_not_contain_secret_patterns() -> None:
    combined = "\n".join(
        [
            _read("README.md"),
            _read("CHANGELOG.md"),
            _read("docs/releases/v0.3.2.md"),
            _read("docs/index.md"),
        ]
    )

    for pattern in SECRET_PATTERNS:
        assert pattern not in combined
    assert not re.search(r"github_pat_[A-Za-z0-9_]+", combined)
