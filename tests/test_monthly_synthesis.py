from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.artifact_paths import daily_data_path
from lattice_digest.monthly_synthesis import build_monthly_synthesis, render_markdown, write_monthly_outputs


def _record(
    title: str,
    abstract: str,
    *,
    label: str = "A",
    score: int = 90,
    reading: int = 80,
    source: str = "arxiv",
    doi: str | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "normalized_title": title.lower(),
        "abstract": abstract,
        "authors": ["Alice Example"],
        "source": source,
        "source_url": f"https://example.org/{title.lower().replace(' ', '-')}",
        "doi": doi,
        "publication_date": "2026-06-02",
        "relevance_label": label,
        "relevance_score": score,
        "reading_priority_score": reading,
        "priority_label": "必须精读" if reading >= 70 else "可略读",
        "keywords_matched": ["LWE", "BKZ"],
        "taxonomy_tags": ["lwe_sis_ntru_foundations"],
    }


def _write_day(data_dir: Path, day: str, records: list[dict[str, object]], *, source_health: list[dict[str, object]] | None = None) -> None:
    payload = {
        "metadata": {"target_date": day},
        "records": records,
        "source_health": source_health
        if source_health is not None
        else [{"source": "arxiv", "health_status": "green", "final_count": len(records)}],
    }
    path = daily_data_path(day, data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_monthly_synthesis_creates_markdown_and_json_for_fixture_month() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        data_dir = root / "data"
        data_dir.mkdir()
        _write_day(
            data_dir,
            "2026-06-01",
            [
                _record(
                    "Hybrid attacks against MLWE-based ML-KEM parameters",
                    "We study MLWE security estimates for ML-KEM. We propose a hybrid attack model with BKZ calibration.",
                    doi="10.1000/mlwe",
                )
            ],
        )
        payload = build_monthly_synthesis(
            data_dir,
            "2026-06",
            generated_at=datetime(2026, 6, 30, tzinfo=timezone.utc),
        )
        json_path, markdown_path = write_monthly_outputs(payload, root / "data", root / "digests")
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        markdown = markdown_path.read_text(encoding="utf-8")

    assert loaded["month"] == "2026-06"
    assert markdown.startswith("# Monthly Lattice Paper Radar — 2026-06")
    assert loaded["total_unique_records"] == 1
    assert loaded["core_papers"][0]["rationale"]["confidence"] == "abstract_supported"
    assert "Core Papers of the Month" in markdown


def test_monthly_missing_days_are_reported_not_silently_ignored() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        data_dir.mkdir()
        _write_day(data_dir, "2026-06-01", [_record("BKZ cost models for LWE", "We study LWE and BKZ.")])

        payload = build_monthly_synthesis(data_dir, "2026-06")

    assert "2026-06-02" in payload["missing_days"]
    assert "2026-06-30" in payload["missing_days"]
    assert payload["TODO_VERIFY"]["missing_daily_files"]


def test_monthly_duplicate_papers_are_deduplicated_and_ordered_by_existing_scores() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        data_dir.mkdir()
        _write_day(data_dir, "2026-06-01", [_record("Module-SIS commitments", "We propose Module-SIS commitments.", score=80, doi="10.1000/sis")])
        _write_day(data_dir, "2026-06-02", [_record("Module-SIS commitments", "We propose Module-SIS commitments.", score=95, source="iacr_eprint", doi="10.1000/sis")])
        _write_day(data_dir, "2026-06-03", [_record("Lower priority PQC overview", "A PQC overview.", label="B", score=70, reading=45)])

        payload = build_monthly_synthesis(data_dir, "2026-06")

    assert payload["total_unique_records"] == 2
    assert payload["core_papers"][0]["title"] == "Module-SIS commitments"
    assert payload["core_papers"][0]["relevance_score"] == 95
    assert payload["core_papers"][0]["seen_dates"] == ["2026-06-01", "2026-06-02"]


def test_monthly_markdown_contains_required_sections() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        data_dir.mkdir()
        _write_day(data_dir, "2026-06-01", [_record("BKZ cost models for LWE", "We study LWE and BKZ attack cost models.")])
        markdown = render_markdown(build_monthly_synthesis(data_dir, "2026-06"))

    for header in [
        "## Executive Summary",
        "## Core Papers of the Month",
        "## Direction Trends",
        "## Reading Priority",
        "## Source Health Summary",
        "## TODO_VERIFY",
    ]:
        assert header in markdown
