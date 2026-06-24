from pathlib import Path

import pytest

from lattice_digest import artifact_paths


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "compat"])
def test_explicit_true_values_enable_legacy_fallback(monkeypatch, value):
    monkeypatch.setenv("LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK", value)
    assert artifact_paths.legacy_fallback_allowed() is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off"])
def test_explicit_false_values_disable_legacy_fallback(monkeypatch, value):
    monkeypatch.setenv("LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK", value)
    assert artifact_paths.legacy_fallback_allowed() is False


def test_explicit_compatibility_resolves_legacy_with_warning(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK", "1")
    canonical = tmp_path / "data" / "2026" / "daily" / "2026-06-23.json"
    legacy = tmp_path / "data" / "2026-06-23.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("{}", encoding="utf-8")

    with pytest.warns(RuntimeWarning, match="Temporary legacy artifact fallback used"):
        resolved, used_legacy = artifact_paths.resolve_existing(canonical, [legacy])

    assert resolved == legacy
    assert used_legacy is True


def test_function_argument_true_overrides_canonical_only_environment(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK", "0")
    canonical = tmp_path / "data" / "2026" / "daily" / "2026-06-23.json"
    legacy = tmp_path / "data" / "2026-06-23.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("{}", encoding="utf-8")

    with pytest.warns(RuntimeWarning):
        resolved, used_legacy = artifact_paths.resolve_existing(
            canonical,
            [legacy],
            allow_legacy_fallback=True,
        )

    assert resolved == legacy
    assert used_legacy is True


def test_function_argument_false_overrides_compatibility_environment(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK", "1")
    canonical = tmp_path / "data" / "2026" / "daily" / "2026-06-23.json"
    legacy = tmp_path / "data" / "2026-06-23.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("{}", encoding="utf-8")

    resolved, used_legacy = artifact_paths.resolve_existing(
        canonical,
        [legacy],
        allow_legacy_fallback=False,
    )

    assert resolved == canonical
    assert used_legacy is False
