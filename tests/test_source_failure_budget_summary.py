from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "summarize_source_failure_budget.py"
SPEC = importlib.util.spec_from_file_location("source_failure_budget", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_pre_tag_evidence_stays_insufficient() -> None:
    assert MODULE.classify_band({"post_tag_run_count": 0, "source_starved_run_count": 0}) == "insufficient_evidence"


def test_source_starved_post_tag_evidence_warns() -> None:
    assert (
        MODULE.classify_band(
            {"post_tag_run_count": 7, "source_starved_run_count": 1, "source_reachability_rate": 0.95}
        )
        == "source_starved_warning"
    )


def test_weekly_metrics_are_traceable(tmp_path: Path) -> None:
    weekly_dir = tmp_path / "data" / "weekly"
    handoff_dir = tmp_path / "handoffs" / "weekly"
    weekly_dir.mkdir(parents=True)
    handoff_dir.mkdir(parents=True)
    (weekly_dir / "2026-W23.json").write_text(
        json.dumps({"coverage": {"expected_days": 7, "loaded_days": ["a", "b", "c", "d", "e"]}}),
        encoding="utf-8",
    )
    (handoff_dir / "2026-W23-handoff-packets.json").write_text(
        json.dumps({"source_weekly_json": "data/weekly/2026-W23.json", "packets": [{}, {}]}),
        encoding="utf-8",
    )

    result = MODULE.weekly_metrics(tmp_path)

    assert result["weekly_coverage_completeness"] == 0.7143
    assert result["handoff_traceability"] is True
    assert result["handoff_packet_count"] == 2
