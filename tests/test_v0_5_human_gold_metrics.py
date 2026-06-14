from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/calculate_v0_5_human_gold_shadow_metrics.py"
SPEC = importlib.util.spec_from_file_location("v0_5_human_gold_metrics", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _gold(sample_id: str, label: str) -> dict:
    return {
        "sample_id": sample_id,
        "human_review_status": "user_confirmed",
        "human_gold_primary_track": label,
        "human_gold_secondary_tracks": [],
        "valid_human_gold": True,
    }


def _prediction(sample_id: str, production: str, shadow: str) -> dict:
    return {
        "sample_id": sample_id,
        "production_primary_track": production,
        "production_secondary_tracks": [],
        "shadow_primary_track": shadow,
        "shadow_secondary_tracks": [],
        "disagreement_category": "exact_match" if production == shadow else "primary_track_disagreement",
    }


def test_metrics_compare_shadow_and_production_only_on_gold_rows() -> None:
    track_a, track_b = MODULE.TRACKS[:2]
    adjudicated = {"records": [_gold("a", track_a), _gold("b", track_b)], "malformed_rows": []}
    shadow = {"records": [_prediction("a", track_b, track_a), _prediction("b", track_b, track_a)]}

    result = MODULE.evaluate(adjudicated, shadow)

    assert result["human_gold_count"] == 2
    assert result["human_gold_metrics_available"] is True
    assert result["shadow_vs_human_gold"]["per_track"][track_a]["tp"] == 1
    assert result["shadow_vs_human_gold"]["per_track"][track_b]["fn"] == 1
    assert result["production_vs_human_gold"]["per_track"][track_b]["tp"] == 1
    assert result["production_vs_human_gold"]["per_track"][track_b]["fp"] == 1


def test_outputs_remain_under_requested_audit_directory(tmp_path: Path) -> None:
    result = MODULE.evaluate({"records": [], "malformed_rows": []}, {"records": []})
    paths = MODULE.write_outputs(result, tmp_path)

    assert paths
    assert all(path.parent == tmp_path for path in paths)
    protected = [(ROOT / name).resolve() for name in ("data", "digests", "handoffs")]
    assert all(not any(root in path.resolve().parents for root in protected) for path in paths)


def test_production_output_directories_are_rejected() -> None:
    result = MODULE.evaluate({"records": [], "malformed_rows": []}, {"records": []})

    for name in ("data", "digests", "handoffs", "src"):
        with pytest.raises(ValueError, match="production path"):
            MODULE.write_outputs(result, ROOT / name / "phase-13h")


def test_metrics_script_is_not_referenced_by_production_or_workflows() -> None:
    name = "calculate_v0_5_human_gold_shadow_metrics"
    paths = list((ROOT / "src/lattice_digest").rglob("*.py"))
    paths += list((ROOT / ".github/workflows").glob("*.yml"))
    paths += list((ROOT / ".github/workflows").glob("*.yaml"))

    assert all(name not in path.read_text(encoding="utf-8") for path in paths)
