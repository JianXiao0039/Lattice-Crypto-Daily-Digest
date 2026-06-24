import pytest

from lattice_digest import artifact_paths


def test_invalid_environment_value_does_not_enable_fallback(monkeypatch):
    monkeypatch.setenv("LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK", "maybe")

    with pytest.warns(RuntimeWarning, match="not recognized"):
        assert artifact_paths.legacy_fallback_allowed() is False
