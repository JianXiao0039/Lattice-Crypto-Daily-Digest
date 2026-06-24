from pathlib import Path

from lattice_digest import artifact_paths


def test_unset_environment_is_canonical_only(monkeypatch):
    monkeypatch.delenv("LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK", raising=False)
    assert artifact_paths.legacy_fallback_allowed() is False


def test_canonical_path_has_priority_even_with_compatibility(tmp_path: Path):
    canonical = tmp_path / "data" / "2026" / "daily" / "2026-06-23.json"
    legacy = tmp_path / "data" / "2026-06-23.json"
    canonical.parent.mkdir(parents=True)
    legacy.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text('{"source":"canonical"}', encoding="utf-8")
    legacy.write_text('{"source":"legacy"}', encoding="utf-8")

    resolved, used_legacy = artifact_paths.resolve_existing(
        canonical,
        [legacy],
        allow_legacy_fallback=True,
    )

    assert resolved == canonical
    assert used_legacy is False


def test_legacy_only_is_rejected_by_new_default(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK", raising=False)
    canonical = tmp_path / "data" / "2026" / "daily" / "2026-06-23.json"
    legacy = tmp_path / "data" / "2026-06-23.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("{}", encoding="utf-8")

    resolved, used_legacy = artifact_paths.resolve_existing(canonical, [legacy])

    assert resolved == canonical
    assert used_legacy is False
    assert not canonical.exists()
