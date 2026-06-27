from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from lattice_digest.artifact_paths import daily_data_path, daily_digest_path
from lattice_digest.models import make_paper_record
from lattice_digest.sources.base import SourceAdapter


def _write_config(root: Path) -> Path:
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        "sources:\n  - name: fake_source\n    type: fake\n    enabled: true\n",
        encoding="utf-8",
    )
    (config_dir / "taxonomy.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "keywords.yaml").write_text("{}", encoding="utf-8")
    (config_dir / "negative_keywords.yaml").write_text("{}", encoding="utf-8")
    return config_dir


def test_date_accepts_iso_date_and_since_still_defaults() -> None:
    import lattice_digest.run as run_module

    date_args = run_module.parse_args(["--date", "2026-06-06"])
    normal_args = run_module.parse_args([])

    assert date_args.date == date(2026, 6, 6)
    assert date_args.since is None
    assert normal_args.date is None
    assert normal_args.since is None


def test_invalid_date_is_rejected() -> None:
    import lattice_digest.run as run_module

    with pytest.raises(SystemExit):
        run_module.parse_args(["--date", "2026-02-30"])


def test_date_and_since_are_rejected_together() -> None:
    import lattice_digest.run as run_module

    with pytest.raises(SystemExit):
        run_module.parse_args(["--date", "2026-06-06", "--since", "7d"])


def test_exact_date_window_is_one_singapore_calendar_day() -> None:
    import lattice_digest.run as run_module

    start, end = run_module._exact_date_coverage_window(date(2026, 6, 6))

    assert start == datetime(2026, 6, 5, 16, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 6, 6, 16, 0, tzinfo=timezone.utc)


def test_date_targeted_run_filters_records_and_writes_exact_date(tmp_path: Path, monkeypatch) -> None:
    import lattice_digest.run as run_module

    config_dir = _write_config(tmp_path)
    inside = make_paper_record(
        title="Inside target date",
        abstract="LWE lattice cryptography",
        source="fake_source",
        source_url="https://example.test/inside",
        publication_date="2026-06-06",
        relevance_label="A",
        relevance_score=90,
    )
    outside = make_paper_record(
        title="Outside target date",
        abstract="LWE lattice cryptography",
        source="fake_source",
        source_url="https://example.test/outside",
        publication_date="2026-06-07",
        relevance_label="A",
        relevance_score=90,
    )

    class FakeSource(SourceAdapter):
        def fetch(self, context):  # type: ignore[no-untyped-def]
            context.set_source_counts(self.name, raw=2, normalized=2, date_filtered=2)
            return [inside, outside]

    monkeypatch.setattr(run_module, "project_root", lambda: tmp_path)
    monkeypatch.setattr(run_module, "build_source", lambda config: FakeSource(config))
    monkeypatch.setattr(run_module, "rank_records", lambda incoming, taxonomy, keywords, negative: list(incoming))

    result = run_module.main(
        [
            "--date",
            "2026-06-06",
            "--output",
            "markdown,json",
            "--send",
            "none",
            "--config-dir",
            str(config_dir),
        ]
    )

    assert result == 0
    json_path = daily_data_path("2026-06-06", tmp_path / "data")
    markdown_path = daily_digest_path("2026-06-06", tmp_path / "digests")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert [record["title"] for record in payload["records"]] == ["Inside target date"]
    assert payload["metadata"]["target_date"] == "2026-06-06"
    assert payload["metadata"]["since_window"] == "24h"
    assert payload["metadata"]["coverage_start"] == "2026-06-05T16:00:00+00:00"
    assert payload["metadata"]["coverage_end"] == "2026-06-06T16:00:00+00:00"
    assert markdown_path.exists()
    assert not (tmp_path / "data" / "2026-06-06.json").exists()
    assert not (tmp_path / "digests" / "2026-06-06.md").exists()


def test_since_behavior_remains_available() -> None:
    import lattice_digest.run as run_module

    args = run_module.parse_args(["--since", "7d"])
    assert args.since == "7d"
    assert args.date is None
