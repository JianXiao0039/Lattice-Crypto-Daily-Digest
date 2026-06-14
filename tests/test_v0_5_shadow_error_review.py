from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/review_v0_5_shadow_errors.py"
SPEC = importlib.util.spec_from_file_location("v0_5_shadow_error_review", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _payload() -> dict:
    return MODULE.review_errors(
        MODULE.load_json(MODULE.DEFAULT_PREDICTIONS),
        MODULE.load_json(MODULE.DEFAULT_SAMPLE),
        MODULE.load_json(MODULE.DEFAULT_RULES),
    )


def test_repository_error_review_remains_non_gold_and_complete() -> None:
    payload = _payload()
    predictions = MODULE.load_json(MODULE.DEFAULT_PREDICTIONS)
    assert payload["pilot_record_count"] == len(predictions["records"])
    assert payload["human_gold_count"] == 0
    assert payload["human_gold_metrics_eligible"] is False
    assert payload["production_shadow_disagreement_count"] == predictions["production_shadow_disagreement_count"]
    assert payload["error_review_status"] == "error_review_complete_without_gold_metrics"
    assert sum(payload["primary_cause_counts"].values()) == payload["reviewed_union_count"]
    assert payload["contributing_cause_counts"].get("author_name_leakage", 0) == 0


def test_error_review_uses_self_contained_evidence_for_broader_pool_rows() -> None:
    predictions = MODULE.load_json(MODULE.DEFAULT_PREDICTIONS)
    static_sample = MODULE.load_json(MODULE.DEFAULT_SAMPLE)
    static_ids = {row["sample_id"] for row in static_sample["records"]}
    broader_rows = [row for row in predictions["records"] if row["sample_id"] not in static_ids]

    assert broader_rows
    assert all("available_evidence" in row for row in broader_rows)
    payload = MODULE.review_errors(predictions, static_sample, MODULE.load_json(MODULE.DEFAULT_RULES))
    assert payload["pilot_record_count"] == len(predictions["records"])


def test_error_review_exposes_track_undercoverage_without_accuracy_claims() -> None:
    payload = _payload()
    track_b = payload["per_track"]["xingye_lu_bridge"]
    assert track_b["codex_reviewed_total"] == 6
    assert track_b.get("shadow_exact", 0) == 0
    assert track_b["shadow_missed"] == 6
    assert payload["shadow_mode_gate"] == "blocked_until_user_annotation"
    assert payload["production_gate"] == "blocked_by_multiple_conditions"


def test_error_review_writes_only_to_explicit_output_directory(tmp_path: Path) -> None:
    paths = MODULE.write_outputs(_payload(), tmp_path / "review")
    assert len(paths) == 9
    assert all(path.is_file() for path in paths)
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "digests").exists()
    assert not (tmp_path / "handoffs").exists()
