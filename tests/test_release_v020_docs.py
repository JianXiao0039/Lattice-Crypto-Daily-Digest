from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = ("ghp_", "github_pat_", "sk-", "xoxb-", "AKIA")


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_v020_release_artifacts_are_archival_docs() -> None:
    assert (ROOT / "docs" / "releases" / "v0.2.0.md").exists()
    assert "v0.2.0" in _read("CHANGELOG.md")


def test_changelog_documents_v020_stable_library_release() -> None:
    changelog = _read("CHANGELOG.md")

    for needle in [
        "v0.2.0",
        "Stable Library Export Layer",
        "Zotero Compatibility Layer",
        "CSL JSON",
        "BibTeX",
        "RIS",
        "Zotero manual import QA workflow",
    ]:
        assert needle in changelog


def test_v020_release_doc_exists_and_states_zotero_boundaries() -> None:
    release_doc = _read("docs/releases/v0.2.0.md")

    assert "Research Library Interoperability Stable Release" in release_doc
    assert "file-based manual import" in release_doc
    assert "当前不是 Zotero XPI plugin" in release_doc or "Zotero XPI plugin" in release_doc
    assert "当前不自动调用 Zotero Web API" in release_doc or "Zotero Web API push" in release_doc


def test_release_checklist_contains_v020_stable_items() -> None:
    checklist = _read("docs/release-checklist.md")

    assert "v0.2.0 Stable Release Checklist" in checklist
    assert "git tag -a v0.2.0" in checklist
    assert "python -m pytest" in checklist
    assert "no `exports/` staged" in checklist
    assert "no `.env` or secrets staged" in checklist


def test_readme_links_v020_stable_docs() -> None:
    readme = _read("README.md")

    for needle in [
        "v0.2.0",
        "Research Library Interoperability Stable Release",
        "Stable Library Export Layer",
        "Zotero Compatibility Layer",
        "Zotero Manual Import QA",
        "docs/releases/v0.2.0.md",
        "docs/library-interop.md",
        "docs/library-export-audit.md",
        "docs/zotero-compat.md",
        "docs/zotero-manual-import.md",
    ]:
        assert needle in readme
    assert "Zotero XPI plugin is not included in v0.2.0" in readme
    assert "Zotero Web API push is not included in v0.2.0" in readme
    assert "file-based manual import" in readme


def test_release_docs_do_not_contain_secret_patterns() -> None:
    combined = "\n".join(
        [
            _read("README.md"),
            _read("CHANGELOG.md"),
            _read("docs/releases/v0.2.0.md"),
            _read("docs/release-checklist.md"),
            _read("docs/library-interop.md"),
            _read("docs/zotero-compat.md"),
            _read("docs/zotero-manual-import.md"),
        ]
    )

    for pattern in SECRET_PATTERNS:
        assert pattern not in combined
    assert not re.search(r"github_pat_[A-Za-z0-9_]+", combined)
