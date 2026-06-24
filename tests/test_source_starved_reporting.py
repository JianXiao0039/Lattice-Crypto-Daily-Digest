from __future__ import annotations

import json
from pathlib import Path

from lattice_digest.artifact_paths import daily_data_path, daily_digest_path, monthly_data_path, monthly_digest_path
from scripts.verify_durable_artifacts import verify_daily, verify_monthly


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_daily_source_starved_run_must_be_explicit(tmp_path: Path) -> None:
    payload = {
        "metadata": {"target_date": "2026-06-15"},
        "records": [],
        "source_health": [
            {"source": "arxiv", "status": "red"},
            {"source": "iacr_eprint", "status": "red"},
        ],
    }
    _write(daily_data_path("2026-06-15", root=tmp_path / "data"), json.dumps(payload))
    _write(daily_digest_path("2026-06-15", root=tmp_path / "digests"), "# 2026-06-15\n\nSource health: all red\n")

    result = verify_daily(tmp_path, "2026-06-15")

    assert result["source_starved"] is True
    assert result["source_starved_explicit"] is False
    assert "source-starved condition is not explicit" in result["TODO_VERIFY"]


def test_daily_source_starved_marker_satisfies_policy(tmp_path: Path) -> None:
    payload = {
        "metadata": {"target_date": "2026-06-15"},
        "records": [],
        "source_health": [
            {"source": "arxiv", "status": "red"},
            {"source": "iacr_eprint", "status": "red"},
        ],
    }
    _write(daily_data_path("2026-06-15", root=tmp_path / "data"), json.dumps(payload))
    _write(daily_digest_path("2026-06-15", root=tmp_path / "digests"), "# 2026-06-15\n\nsource-starved: true\n")

    result = verify_daily(tmp_path, "2026-06-15")

    assert result["source_starved"] is True
    assert result["source_starved_explicit"] is True


def test_monthly_source_starved_status_is_required(tmp_path: Path) -> None:
    payload = {
        "month": "2026-06",
        "input_daily_files": [],
        "missing_days": ["2026-06-01"],
        "source_health_summary": {"sources": []},
    }
    _write(monthly_data_path("2026-06", root=tmp_path / "data"), json.dumps(payload))
    _write(monthly_digest_path("2026-06", root=tmp_path / "digests"), "# Monthly Lattice Paper Radar — 2026-06\n")

    result = verify_monthly(tmp_path, "2026-06")

    assert result["source_starved_explicit"] is False
    assert "monthly source-starved status missing" in result["TODO_VERIFY"]
