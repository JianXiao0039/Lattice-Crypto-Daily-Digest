from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA")


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_version_field_contains_v020rc1() -> None:
    pyproject = _read("pyproject.toml")
    init = _read("src/lattice_digest/__init__.py")

    assert 'version = "0.2.0rc1"' in pyproject or "0.2.0-rc1" in pyproject
    assert '__version__ = "0.2.0rc1"' in init or "0.2.0-rc1" in init


def test_changelog_documents_v020rc1_library_export() -> None:
    changelog = _read("CHANGELOG.md")

    for needle in [
        "v0.2.0-rc1",
        "Stable Library Export Layer",
        "CSL JSON",
        "BibTeX",
        "RIS",
        "Zotero-ready export",
    ]:
        assert needle in changelog


def test_release_doc_exists_and_states_rc_limitations() -> None:
    release_doc = _read("docs/releases/v0.2.0-rc1.md")

    assert "Release Candidate" in release_doc
    assert "Zotero XPI plugin is not included" in release_doc or "不包含 Zotero XPI plugin" in release_doc
    assert "Current Zotero workflow is manual file import" in release_doc or "文件式手动导入" in release_doc


def test_release_checklist_contains_v020rc1_tag_command() -> None:
    checklist = _read("docs/release-checklist.md")

    assert "v0.2.0-rc1 Release Candidate Checklist" in checklist
    assert "git tag -a v0.2.0-rc1" in checklist
    assert "python -m pytest" in checklist


def test_readme_links_v020rc1_and_library_interop() -> None:
    readme = _read("README.md")

    for needle in [
        "v0.2.0-rc1",
        "Library Interoperability Release Candidate",
        "Stable Library Export Layer",
        "Zotero-ready export",
        "CSL JSON",
        "BibTeX",
        "RIS",
        "docs/library-interop.md",
        "docs/releases/v0.2.0-rc1.md",
    ]:
        assert needle in readme
    assert "Zotero XPI plugin is not included in v0.2.0-rc1" in readme
    assert "file-based manual import" in readme


def test_release_docs_do_not_contain_secret_patterns() -> None:
    combined = "\n".join(
        [
            _read("README.md"),
            _read("CHANGELOG.md"),
            _read("docs/releases/v0.2.0-rc1.md"),
            _read("docs/release-checklist.md"),
            _read("docs/library-interop.md"),
        ]
    )

    for pattern in SECRET_PATTERNS:
        assert pattern not in combined
    assert not re.search(r"github_pat_[A-Za-z0-9_]+", combined)
