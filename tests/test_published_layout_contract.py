"""Reuse P0's positive/negative deployment contract controls without its unrelated changes."""
import sys
import pytest
from lattice_digest.runtime_paths import RuntimePaths
from lattice_digest.public_contract import validate_public_paths
from scripts.verify_v0_4_1_release_candidate import read_versions

def test_src_layout_without_bridge_and_present_bridge_is_checked(tmp_path):
    (tmp_path/'src/lattice_digest').mkdir(parents=True)
    (tmp_path/'pyproject.toml').write_text('[project]\nversion="0.4.1"')
    (tmp_path/'src/lattice_digest/__init__.py').write_text('__version__ = "0.4.1"')
    assert read_versions(tmp_path)=={'pyproject':'0.4.1','source_package':'0.4.1'}
    (tmp_path/'lattice_digest').mkdir()
    (tmp_path/'lattice_digest/__init__.py').write_text('__version__ = "invalid-old"')
    assert read_versions(tmp_path)['bridge_package']=='invalid-old'
    (tmp_path/'src/lattice_digest/__init__.py').write_text('broken = True')
    with pytest.raises(ValueError,match='missing __version__'):read_versions(tmp_path)

def test_canonical_resolution_never_defaults_to_code_when_explicit(tmp_path):
    code,canonical=tmp_path/'code',tmp_path/'artifacts'
    paths=RuntimePaths.resolve(code_root=code,environ={'LATTICE_DIGEST_CANONICAL_ROOT':str(canonical)})
    assert paths.database_path==canonical/'papers.db'
    assert paths.config_root==code/'config'
    assert not paths.database_path.is_relative_to(code)

def test_clean_import_path_and_development_path_rejection(tmp_path,monkeypatch):
    code,canonical=tmp_path/'code',tmp_path/'artifacts';code.mkdir();canonical.mkdir()
    monkeypatch.chdir(code);monkeypatch.setenv('LATTICE_DIGEST_CANONICAL_ROOT',str(canonical));monkeypatch.setenv('PYTHONPATH',str(code/'src'))
    monkeypatch.setattr(sys,'path',[str(code),str(code/'src')]);paths=RuntimePaths.resolve(code_root=code,canonical_root=canonical);validate_public_paths(paths)
    monkeypatch.setattr(sys,'path',[str(code),str(canonical/'src')])
    with pytest.raises(ValueError,match='development root'):validate_public_paths(paths)
    monkeypatch.setattr(sys,'path',[str(code)]);(code/'papers.db').write_bytes(b'forbidden second database')
    with pytest.raises(ValueError,match='runtime-local artifact'):validate_public_paths(paths)
