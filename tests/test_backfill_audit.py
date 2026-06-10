from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_backfill_2026_06_04_to_2026_06_10.py"
SPEC = importlib.util.spec_from_file_location("audit_backfill", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_daily(root: Path, date: str, records: list[dict], source_health: list[dict]) -> None:
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "digests").mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {"target_date": date, "total_records": len(records)},
        "records": records,
        "source_health": source_health,
    }
    (root / "data" / f"{date}.json").write_text(json.dumps(payload), encoding="utf-8")
    (root / "digests" / f"{date}.md").write_text("# digest\n", encoding="utf-8")


def test_source_starved_and_missing_days_are_detected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(MODULE, "git_log_for_path", lambda project_root, relative_path: [])
    all_red = [{"source": name, "status": "red", "retryable": True} for name in ("arxiv", "iacr_eprint")]
    write_daily(tmp_path, "2026-06-04", [], all_red)

    row = MODULE.audit_date(tmp_path, "2026-06-04")
    missing = MODULE.audit_date(tmp_path, "2026-06-05")

    assert row["source_starved"] is True
    assert "source-starved run" in "; ".join(row["TODO_VERIFY"])
    assert missing["data_json_exists"] is False
    assert "data JSON missing" in missing["TODO_VERIFY"]


def test_summary_marks_incomplete_window_as_insufficient_evidence() -> None:
    rows = [
        {"date": "2026-06-04", "data_json_exists": True, "digest_markdown_exists": True, "source_starved": False, "source_red_count": 0},
        {"date": "2026-06-05", "data_json_exists": False, "digest_markdown_exists": False, "source_starved": False, "source_red_count": 0},
        {"date": "2026-06-10", "data_json_exists": True, "digest_markdown_exists": True, "source_starved": False, "source_red_count": 0},
    ]
    decision = MODULE.summarize_decision(rows)
    assert decision["daily_decision"] == "insufficient_evidence"
    assert decision["weekly_decision"] == "keep_active_with_source_starved_warning"
