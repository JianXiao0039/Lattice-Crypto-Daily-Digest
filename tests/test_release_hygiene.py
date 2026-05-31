from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_release_hygiene.py"

spec = importlib.util.spec_from_file_location("check_release_hygiene", SCRIPT_PATH)
assert spec and spec.loader
hygiene = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hygiene)


def test_release_metadata_hygiene_matches_current_version() -> None:
    version = hygiene._read_current_version()
    hygiene._check_release_docs(version)
    assert version
    assert (ROOT / "docs" / "releases" / f"v{version}.md").exists()


def test_forbidden_staged_generated_artifacts_are_detected() -> None:
    staged = [
        "exports/library/library-items.json",
        "audits/library-export/report.md",
        ".pytest_tmp/tmp/data.json",
        "data/2026-05-31.json",
        "digests/2026-05-31.md",
        "papers.db",
        ".env",
        "state/reading-queue.json",
        "src/lattice_digest/storage.py",
    ]

    blocked = hygiene.forbidden_staged_paths(staged)

    assert "src/lattice_digest/storage.py" not in blocked
    for path in staged[:-1]:
        assert path in blocked


def test_tracked_guard_blocks_runtime_dirs_by_default() -> None:
    tracked = [
        "exports/zotero/items.csl.json",
        "audits/library-export/report.md",
        ".env",
        "state/reading-queue.lock",
        "src/lattice_digest/storage.py",
        "data/2026-05-30.json",
        "digests/2026-05-30.md",
        "papers.db",
    ]

    blocked = hygiene.forbidden_tracked_paths(tracked, strict_generated=False)

    assert "exports/zotero/items.csl.json" in blocked
    assert "audits/library-export/report.md" in blocked
    assert ".env" in blocked
    assert "state/reading-queue.lock" in blocked
    assert "src/lattice_digest/storage.py" not in blocked
    assert "data/2026-05-30.json" not in blocked
    assert "digests/2026-05-30.md" not in blocked
    assert "papers.db" not in blocked


def test_strict_tracked_guard_can_block_legacy_digest_artifacts() -> None:
    tracked = ["data/2026-05-30.json", "digests/2026-05-30.md", "papers.db"]

    blocked = hygiene.forbidden_tracked_paths(tracked, strict_generated=True)

    assert blocked == ["data/2026-05-30.json", "digests/2026-05-30.md", "papers.db"]
