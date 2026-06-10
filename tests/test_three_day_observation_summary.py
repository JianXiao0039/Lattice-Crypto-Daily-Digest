from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "summarize_three_day_observation.py"
SPEC = importlib.util.spec_from_file_location("summarize_three_day_observation", SCRIPT_PATH)
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


def test_source_starved_when_empty_and_all_red(tmp_path: Path) -> None:
    source_health = [
        {"source": "arxiv", "status": "red", "retryable": True},
        {"source": "iacr_eprint", "status": "red", "latest_feed_status": "failed"},
    ]
    write_daily(tmp_path, "2026-06-08", [], source_health)
    summary = MODULE.build_summary(project_root=tmp_path, count=1)
    observation = summary["observations"][0]
    assert observation["source_starved"] is True
    assert observation["reliability_verdict"] == "source_starved"


def test_latest_three_artifacts_are_selected(tmp_path: Path) -> None:
    green = [{"source": "arxiv", "status": "green"}]
    for date in ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]:
        write_daily(tmp_path, date, [{"relevance_label": "A"}], green)
    summary = MODULE.build_summary(project_root=tmp_path, count=3)
    assert summary["observed_dates"] == ["2026-06-02", "2026-06-03", "2026-06-04"]
    assert summary["observations"][0]["high_priority_count"] == 1
