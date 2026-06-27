from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_durable_artifacts import verify_artifacts, verify_daily
from lattice_digest.artifact_paths import daily_data_path, daily_digest_path, weekly_data_path, weekly_digest_path, monthly_data_path, monthly_digest_path


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_durable_verifier_detects_missing_markdown_json_pair(tmp_path: Path) -> None:
    _write(daily_data_path("2026-06-15", tmp_path / "data"), '{"records": [], "source_health": []}')

    report = verify_artifacts(tmp_path, target_date="2026-06-15", week=None, month=None)

    daily = report["checks"][0]
    assert daily["markdown_exists"] is False
    assert daily["json_exists"] is True
    assert report["overall_status"] == "partial_or_missing"


def test_durable_verifier_detects_invalid_json(tmp_path: Path) -> None:
    _write(daily_data_path("2026-06-15", tmp_path / "data"), "{not-json")
    _write(daily_digest_path("2026-06-15", tmp_path / "digests"), "# 2026-06-15\n\nSource health: present\n")

    daily = verify_daily(tmp_path, "2026-06-15")

    assert daily["json_parseable"] is False
    assert str(daily["json_error"]).startswith("invalid_json")


def test_durable_verifier_accepts_daily_weekly_monthly_artifacts(tmp_path: Path) -> None:
    daily_payload = {
        "metadata": {"target_date": "2026-06-15"},
        "records": [{"title": "x"}],
        "source_health": [{"source": "arxiv", "status": "green"}],
    }
    weekly_payload = {
        "generated_at": "2026-06-15T00:00:00+00:00",
        "coverage": {"input_dates": ["2026-06-15"]},
        "source_health_summary": {"available": True, "sources": []},
    }
    monthly_payload = {
        "month": "2026-06",
        "input_daily_files": ["data/2026/daily/2026-06-15.json"],
        "missing_days": [],
        "source_health_summary": {"source_starved": False, "sources": []},
    }
    _write(daily_data_path("2026-06-15", tmp_path / "data"), json.dumps(daily_payload))
    _write(daily_digest_path("2026-06-15", tmp_path / "digests"), "# 2026-06-15\n\nSource health: green\n")
    _write(weekly_data_path("2026-W25", root=tmp_path / "data"), json.dumps(weekly_payload))
    _write(weekly_digest_path("2026-W25", root=tmp_path / "digests"), "# Weekly 2026-W25\n\nSource health: green\n")
    _write(monthly_data_path("2026-06", root=tmp_path / "data"), json.dumps(monthly_payload))
    _write(monthly_digest_path("2026-06", root=tmp_path / "digests"), "# Monthly Lattice Paper Radar — 2026-06\n")

    report = verify_artifacts(tmp_path, target_date="2026-06-15", week="2026-W25", month="2026-06")

    assert report["overall_status"] == "verified"
    assert [check["kind"] for check in report["checks"]] == ["daily", "weekly", "monthly"]
