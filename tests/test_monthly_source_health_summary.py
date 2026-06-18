from __future__ import annotations

import json
import py_compile
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.monthly_synthesis import build_monthly_synthesis


ROOT = Path(__file__).resolve().parents[1]


def _write_payload(data_dir: Path, day: str, payload: dict[str, object]) -> None:
    (data_dir / f"{day}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_monthly_source_health_summary_handles_missing_audit_records() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        data_dir.mkdir()
        _write_payload(data_dir, "2026-06-01", {"metadata": {"target_date": "2026-06-01"}, "records": []})

        payload = build_monthly_synthesis(data_dir, "2026-06")

    sources = {row["source"]: row for row in payload["source_health_summary"]["sources"]}
    assert sources["arxiv"]["days_observed"] == 0
    assert sources["arxiv"]["impact"] == "no source-health records found for this month"
    assert payload["TODO_VERIFY"]["missing_source_health_records"] == ["2026-06-01"]


def test_monthly_source_health_summary_detects_source_starved_day() -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "data"
        data_dir.mkdir()
        _write_payload(
            data_dir,
            "2026-06-01",
            {
                "metadata": {"target_date": "2026-06-01"},
                "records": [],
                "source_health": [
                    {"source": "arxiv", "health_status": "red", "error_type": "network"},
                    {"source": "iacr_eprint", "health_status": "red", "error_type": "network"},
                ],
            },
        )

        payload = build_monthly_synthesis(data_dir, "2026-06")

    assert payload["source_health_summary"]["source_starved"] is True
    assert payload["source_health_summary"]["source_starved_days"] == ["2026-06-01"]
    sources = {row["source"]: row for row in payload["source_health_summary"]["sources"]}
    assert sources["arxiv"]["failure_types"] == {"network": 1}


def test_monthly_synthesis_python311_compatible_and_noninterfering() -> None:
    py_compile.compile(str(ROOT / "src" / "lattice_digest" / "monthly_synthesis.py"), doraise=True)
    for relative in [
        "src/lattice_digest/ranker.py",
        "src/lattice_digest/digest_sections.py",
        "src/lattice_digest/library_taxonomy.py",
    ]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "monthly_synthesis" not in text
