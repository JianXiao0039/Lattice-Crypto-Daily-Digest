from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_release_hygiene.py"

spec = importlib.util.spec_from_file_location("check_release_hygiene", SCRIPT_PATH)
assert spec and spec.loader
hygiene = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hygiene)


def write_pair(root: Path, legacy: str, canonical: str, *, legacy_text: str = '{"ok": true}', canonical_text: str = '{"ok": true}') -> None:
    legacy_path = root / legacy
    canonical_path = root / canonical
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_text(legacy_text, encoding="utf-8")
    canonical_path.write_text(canonical_text, encoding="utf-8")


def configure_root(monkeypatch, tmp_path: Path, *, ignored: set[str] | None = None) -> None:
    ignored = ignored or set()
    monkeypatch.setattr(hygiene, "ROOT", tmp_path)
    monkeypatch.setattr(hygiene, "_is_ignored", lambda path: path in ignored)


def test_valid_index_only_untracking_passes(monkeypatch, tmp_path: Path) -> None:
    legacy = "data/2026-05-22.json"
    canonical = "data/2026/daily/2026-05-22.json"
    write_pair(tmp_path, legacy, canonical)
    configure_root(monkeypatch, tmp_path, ignored={legacy})

    blocked, accepted = hygiene.migration_aware_staged_hygiene([("D", legacy)])

    assert blocked == []
    assert accepted == [f"{legacy}:authorized_generated_artifact_untracking_verified"]


def test_physical_legacy_file_missing_fails(monkeypatch, tmp_path: Path) -> None:
    legacy = "data/2026-05-22.json"
    canonical = "data/2026/daily/2026-05-22.json"
    (tmp_path / canonical).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / canonical).write_text('{"ok": true}', encoding="utf-8")
    configure_root(monkeypatch, tmp_path, ignored={legacy})

    blocked, accepted = hygiene.migration_aware_staged_hygiene([("D", legacy)])

    assert accepted == []
    assert blocked == [f"{legacy}:legacy_working_tree_file_missing"]


def test_canonical_counterpart_missing_fails(monkeypatch, tmp_path: Path) -> None:
    legacy = "data/2026-05-22.json"
    (tmp_path / legacy).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / legacy).write_text('{"ok": true}', encoding="utf-8")
    configure_root(monkeypatch, tmp_path, ignored={legacy})

    blocked, _ = hygiene.migration_aware_staged_hygiene([("D", legacy)])

    assert blocked == [f"{legacy}:canonical_counterpart_missing"]


def test_canonical_counterpart_invalid_fails(monkeypatch, tmp_path: Path) -> None:
    legacy = "data/2026-05-22.json"
    canonical = "data/2026/daily/2026-05-22.json"
    write_pair(tmp_path, legacy, canonical, canonical_text="{not json")
    configure_root(monkeypatch, tmp_path, ignored={legacy})

    blocked, _ = hygiene.migration_aware_staged_hygiene([("D", legacy)])

    assert blocked == [f"{legacy}:canonical_json_invalid"]


def test_hash_mismatch_fails(monkeypatch, tmp_path: Path) -> None:
    legacy = "data/2026-05-22.json"
    canonical = "data/2026/daily/2026-05-22.json"
    write_pair(tmp_path, legacy, canonical, legacy_text='{"ok": true}', canonical_text='{"ok": false}')
    configure_root(monkeypatch, tmp_path, ignored={legacy})

    blocked, _ = hygiene.migration_aware_staged_hygiene([("D", legacy)])

    assert blocked == [f"{legacy}:legacy_canonical_hash_mismatch"]


def test_logical_identifier_mismatch_fails(monkeypatch, tmp_path: Path) -> None:
    legacy = "data/not-a-date.json"
    (tmp_path / legacy).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / legacy).write_text('{"ok": true}', encoding="utf-8")
    configure_root(monkeypatch, tmp_path, ignored={legacy})

    blocked, _ = hygiene.migration_aware_staged_hygiene([("D", legacy)])

    assert blocked == [f"{legacy}:not_a_recognized_legacy_generated_json_path"]


def test_legacy_path_not_ignored_fails(monkeypatch, tmp_path: Path) -> None:
    legacy = "data/monthly/2026-06.json"
    canonical = "data/2026/monthly/2026-06.json"
    write_pair(tmp_path, legacy, canonical)
    configure_root(monkeypatch, tmp_path, ignored=set())

    blocked, _ = hygiene.migration_aware_staged_hygiene([("D", legacy)])

    assert blocked == [f"{legacy}:legacy_path_not_ignored_after_untracking"]


def test_canonical_counterpart_staged_fails(monkeypatch, tmp_path: Path) -> None:
    legacy = "data/weekly/2026-W22.json"
    canonical = "data/2026/weekly/2026-W22.json"
    write_pair(tmp_path, legacy, canonical)
    configure_root(monkeypatch, tmp_path, ignored={legacy})

    blocked, _ = hygiene.migration_aware_staged_hygiene([("D", legacy), ("A", canonical)])

    assert f"{legacy}:canonical_counterpart_is_staged" in blocked
    assert canonical in blocked


def test_unrelated_staged_deletion_fails(monkeypatch, tmp_path: Path) -> None:
    configure_root(monkeypatch, tmp_path)

    blocked, _ = hygiene.migration_aware_staged_hygiene([("D", "docs/some-report.md")])

    assert blocked == ["docs/some-report.md:unverified_staged_deletion"]


def test_source_code_deletion_fails(monkeypatch, tmp_path: Path) -> None:
    configure_root(monkeypatch, tmp_path)

    blocked, _ = hygiene.migration_aware_staged_hygiene([("D", "src/lattice_digest/run.py")])

    assert blocked == ["src/lattice_digest/run.py:source_code_deletion"]


def test_ordinary_legacy_generated_artifact_addition_still_fails(monkeypatch, tmp_path: Path) -> None:
    configure_root(monkeypatch, tmp_path)

    blocked, _ = hygiene.migration_aware_staged_hygiene([("A", "data/2026-05-22.json")])

    assert blocked == ["data/2026-05-22.json"]


def test_no_git_write_operation_is_embedded() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "git add" not in source
    assert "git rm" not in source
    assert "git commit" not in source
