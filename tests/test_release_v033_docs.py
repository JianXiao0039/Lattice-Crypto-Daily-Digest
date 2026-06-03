from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA")


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_version_sources_are_v033() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    src_init = _read("src/lattice_digest/__init__.py")
    bridge_path = ROOT / "lattice_digest" / "__init__.py"

    assert pyproject["project"]["version"] == "0.3.3"
    assert '__version__ = "0.3.3"' in src_init
    if bridge_path.exists():
        assert '__version__ = "0.3.3"' in bridge_path.read_text(encoding="utf-8")


def test_v033_release_doc_and_changelog_exist() -> None:
    assert (ROOT / "docs" / "releases" / "v0.3.3.md").exists()
    assert "v0.3.3" in _read("CHANGELOG.md")


def test_readme_links_v033_release_and_docs_index() -> None:
    readme = _read("README.md")

    assert "docs/releases/v0.3.3.md" in readme
    assert "docs/index.md" in readme
    assert "v0.3.3 maintenance release" in readme


def test_v033_release_notes_cover_expected_maintenance_scope() -> None:
    release_doc = _read("docs/releases/v0.3.3.md")

    for needle in [
        "IACR failed attempt manual retry recovery",
        "IACR latest/RSS source recovery",
        "latest-feed observability",
        "Cross-source latest/query/enrichment audit",
        "Source query coverage audit",
        "Optional Semantic Scholar metadata enrichment",
        "SEMANTIC_SCHOLAR_API_KEY",
        "Research report quality polish",
        "lattice/PQC anchor evidence",
        "No scheduled automation",
        "Windows Task Scheduler",
        "cron",
        "startup task",
        "background service",
        "No ranking threshold changes",
        "No taxonomy semantic changes",
        "Semantic Scholar citation metadata is advisory only",
    ]:
        assert needle in release_doc


def test_v033_changelog_mentions_expected_release_scope() -> None:
    changelog = _read("CHANGELOG.md")

    for needle in [
        "v0.3.3",
        "IACR failed attempt manual retry recovery",
        "IACR latest/RSS source recovery",
        "latest-feed observability",
        "Cross-source latest/query/enrichment audit",
        "Source query coverage audit",
        "Optional Semantic Scholar metadata enrichment",
        "SEMANTIC_SCHOLAR_API_KEY",
        "Research report quality polish",
        "lattice/PQC anchor evidence",
        "Manual quality-first workflow remains supported",
        "No scheduled automation is added",
        "No ranking threshold changes",
        "No taxonomy semantic changes",
        "Semantic Scholar citation metadata is advisory only",
    ]:
        assert needle in changelog


def test_v033_readme_mentions_optional_semantic_scholar_without_secret() -> None:
    readme = _read("README.md")

    assert "optional Semantic Scholar metadata enrichment" in readme
    assert "SEMANTIC_SCHOLAR_API_KEY" in readme
    assert "Citation metadata is advisory only" in readme
    assert "No scheduled automation is configured" in readme


def test_v033_release_docs_do_not_contain_secret_patterns() -> None:
    combined = "\n".join(
        [
            _read("README.md"),
            _read("CHANGELOG.md"),
            _read("docs/releases/v0.3.3.md"),
            _read("docs/index.md"),
        ]
    )

    for pattern in SECRET_PATTERNS:
        assert pattern not in combined
    assert not re.search(r"github_pat_[A-Za-z0-9_]+", combined)
