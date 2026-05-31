from __future__ import annotations

from pathlib import Path

import lattice_digest.storage as storage
from lattice_digest.models import make_paper_record


class _FakeConnection:
    def __init__(self, *, fail_on_execute: bool = False) -> None:
        self.fail_on_execute = fail_on_execute
        self.executed = 0
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        self.executed += 1
        if self.fail_on_execute:
            raise RuntimeError("simulated sqlite failure")
        return None

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


def _record():
    return make_paper_record(
        title="BKZ cleanup test for LWE",
        abstract="A lattice cryptanalysis paper about BKZ and LWE.",
        source="fake_source",
        source_url="https://example.test/bkz-cleanup",
        publication_date="2026-05-31",
        relevance_label="A",
        relevance_score=90,
    )


def test_write_sqlite_closes_connection_on_success() -> None:
    fake = _FakeConnection()
    original_connect = storage.sqlite3.connect
    try:
        storage.sqlite3.connect = lambda path: fake  # type: ignore[assignment]
        storage.write_sqlite([_record()], Path("papers.db"))
    finally:
        storage.sqlite3.connect = original_connect  # type: ignore[assignment]

    assert fake.committed is True
    assert fake.rolled_back is False
    assert fake.closed is True


def test_write_sqlite_closes_connection_on_error() -> None:
    fake = _FakeConnection(fail_on_execute=True)
    original_connect = storage.sqlite3.connect
    try:
        storage.sqlite3.connect = lambda path: fake  # type: ignore[assignment]
        try:
            storage.write_sqlite([_record()], Path("papers.db"))
        except RuntimeError as exc:
            assert "simulated sqlite failure" in str(exc)
        else:
            raise AssertionError("write_sqlite should re-raise sqlite write errors")
    finally:
        storage.sqlite3.connect = original_connect  # type: ignore[assignment]

    assert fake.committed is False
    assert fake.rolled_back is True
    assert fake.closed is True
