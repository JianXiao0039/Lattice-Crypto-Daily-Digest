"""Python 3.11 lexical-route protection without Path.is_junction support."""
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace

import pytest

from lattice_digest.public_contract import _reject_redirects
from lattice_digest.period_delivery import writer_lock


REPARSE_POINT = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)


def remove_junction_method(monkeypatch, path):
    # Remove the real defining class, including pathlib versions with inheritance.
    for cls in type(path).__mro__:
        if 'is_junction' in cls.__dict__:
            monkeypatch.delattr(cls, 'is_junction')
    assert not hasattr(path, 'is_junction')


def fake_lstat(monkeypatch, selected, *, attributes=REPARSE_POINT, mode=stat.S_IFDIR):
    actual = Path.lstat

    def lstat(path, *args, **kwargs):
        if path == selected:
            return SimpleNamespace(st_mode=mode, st_file_attributes=attributes)
        return actual(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'lstat', lstat)


@pytest.mark.parametrize('route', ['redirect', '.ops/runtime/published'])
@pytest.mark.parametrize('missing_leaf', [False, True])
def test_311_reparse_attributes_reject_leaf_and_lexical_ancestors(tmp_path, monkeypatch, route, missing_leaf):
    remove_junction_method(monkeypatch, tmp_path)
    redirect = tmp_path / route
    redirect.mkdir(parents=True)
    fake_lstat(monkeypatch, redirect)
    target = redirect / 'not-yet-created' / 'artifact.json' if missing_leaf else redirect
    with pytest.raises(ValueError, match='path redirect is forbidden'):
        _reject_redirects(target)


@pytest.mark.parametrize('attributes', [0, 1, 0x10, 0x20])
def test_311_regular_ntfs_attributes_and_missing_output_are_allowed(tmp_path, monkeypatch, attributes):
    remove_junction_method(monkeypatch, tmp_path)
    ordinary = tmp_path / 'ordinary'
    ordinary.mkdir()
    fake_lstat(monkeypatch, ordinary, attributes=attributes)
    _reject_redirects(ordinary / 'missing' / 'output.json')


def test_nonwindows_stat_without_ntfs_attributes_is_allowed(tmp_path, monkeypatch):
    remove_junction_method(monkeypatch, tmp_path)
    actual = Path.lstat

    def lstat(path, *args, **kwargs):
        if path == tmp_path:
            return SimpleNamespace(st_mode=stat.S_IFDIR)
        return actual(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'lstat', lstat)
    _reject_redirects(tmp_path / 'new.json')


def test_311_symbolic_link_mode_is_rejected_without_native_helpers(tmp_path, monkeypatch):
    remove_junction_method(monkeypatch, tmp_path)
    fake_lstat(monkeypatch, tmp_path, attributes=0, mode=stat.S_IFLNK)
    with pytest.raises(ValueError, match='redirect'):
        _reject_redirects(tmp_path / 'new.json')


def test_lstat_permission_failure_is_not_treated_as_missing_or_regular(tmp_path, monkeypatch):
    actual = Path.lstat

    def lstat(path, *args, **kwargs):
        if path == tmp_path:
            raise PermissionError('unreadable lexical route')
        return actual(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'lstat', lstat)
    with pytest.raises(PermissionError, match='unreadable lexical route'):
        _reject_redirects(tmp_path / 'new.json')


@pytest.mark.parametrize('redirect_parent', [False, True])
def test_311_writer_lock_rejects_reparse_directory_or_ancestor(tmp_path, monkeypatch, redirect_parent):
    remove_junction_method(monkeypatch, tmp_path)
    audit = tmp_path / 'audits'
    audit.mkdir()
    redirect = audit if redirect_parent else audit / 'writer-locks'
    if not redirect_parent:
        redirect.mkdir()
    fake_lstat(monkeypatch, redirect)
    with pytest.raises(ValueError, match='writer lock redirection forbidden'):
        with writer_lock(SimpleNamespace(audit_root=audit), 'DAILY', '2026-10-19'):
            pytest.fail('redirected lock must never be acquired')
    assert not list(tmp_path.rglob('*.lock'))


@pytest.mark.skipif(os.name != 'nt', reason='Actual NTFS junction requires Windows')
@pytest.mark.parametrize('missing_leaf', [False, True])
def test_real_windows_junction_rejected_without_is_junction(tmp_path, monkeypatch, missing_leaf):
    remove_junction_method(monkeypatch, tmp_path)
    outside = tmp_path / 'outside'
    outside.mkdir()
    sentinel = outside / 'preserved.txt'
    sentinel.write_bytes(b'ORIGINAL')
    link = tmp_path / 'redirect'
    result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], capture_output=True)
    assert result.returncode == 0, result.stderr
    try:
        # lstat must expose the reparse bit even when pathlib has no junction API.
        assert link.lstat().st_file_attributes & REPARSE_POINT
        with pytest.raises(ValueError, match='path redirect is forbidden'):
            _reject_redirects(link / 'not-yet-created' / 'report.json' if missing_leaf else link)
        assert sentinel.read_bytes() == b'ORIGINAL'
    finally:
        os.rmdir(link)  # Remove only this fixture link, never its destination.


@pytest.mark.skipif(os.name != 'nt', reason='Actual NTFS junction requires Windows')
@pytest.mark.parametrize('redirect_parent', [False, True])
def test_real_windows_junction_writer_lock_rejects_without_is_junction(tmp_path, monkeypatch, redirect_parent):
    remove_junction_method(monkeypatch, tmp_path)
    outside = tmp_path / 'outside'
    outside.mkdir()
    audit = tmp_path / 'audits'
    if not redirect_parent:
        audit.mkdir()
    link = audit if redirect_parent else audit / 'writer-locks'
    result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], capture_output=True)
    assert result.returncode == 0, result.stderr
    try:
        with pytest.raises(ValueError, match='writer lock redirection forbidden'):
            with writer_lock(SimpleNamespace(audit_root=audit), 'DAILY', '2026-10-19'):
                pytest.fail('redirected lock must never be acquired')
        assert list(outside.iterdir()) == []
    finally:
        os.rmdir(link)  # Remove only this fixture link, never its destination.
