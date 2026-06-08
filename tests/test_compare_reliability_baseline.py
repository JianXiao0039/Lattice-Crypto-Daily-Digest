from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "compare_reliability_baseline.py"
SPEC = importlib.util.spec_from_file_location("compare_reliability_baseline", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_load_frozen_baseline_from_text_extracts_json_block() -> None:
    text = """
# Report

```json
{"baseline_date": "2026-06-08", "source_total_count": 6}
```
"""
    payload = MODULE.load_frozen_baseline_from_text(text)
    assert payload["baseline_date"] == "2026-06-08"
    assert payload["source_total_count"] == 6


def test_compare_metric_handles_missing_baseline_value() -> None:
    status, interpretation = MODULE.compare_metric("generated_artifacts_present", None, True)
    assert status == "unknown_due_to_missing_artifacts"
    assert "missing" in interpretation


def test_build_diff_rows_marks_statuses() -> None:
    baseline = {
        "source_green_count": 2,
        "source_red_count": 1,
        "semantic_scholar_enrichment_status": "no_candidates_to_enrich",
        "source_starved_true_false": False,
        "generated_artifacts_present": None,
        "validation_passed": True,
        "manual_recovery_needed": False,
    }
    current = {
        "source_green_count": 3,
        "source_red_count": 0,
        "semantic_scholar_enrichment_status": "rate_limit",
        "source_starved_true_false": False,
        "generated_artifacts_present": True,
        "validation_passed": True,
        "manual_recovery_needed": False,
    }
    rows = MODULE.build_diff_rows(baseline, current)
    by_metric = {row["metric"]: row for row in rows}
    assert by_metric["source_green_count"]["status"] == "improved"
    assert by_metric["source_red_count"]["status"] == "improved"
    assert by_metric["semantic_scholar_enrichment_status"]["status"] == "degraded"
    assert by_metric["generated_artifacts_present"]["status"] == "unknown_due_to_missing_artifacts"
