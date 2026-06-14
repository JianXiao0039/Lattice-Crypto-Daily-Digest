from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/calculate_v0_5_human_gold_shadow_metrics.py"
SPEC = importlib.util.spec_from_file_location("v0_5_no_gold_metrics", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_no_gold_does_not_emit_final_precision_recall_or_f1(tmp_path: Path) -> None:
    adjudicated = {
        "records": [
            {
                "sample_id": "queued",
                "human_review_status": "queued_for_user",
                "human_gold_primary_track": None,
                "human_gold_secondary_tracks": [],
                "valid_human_gold": False,
            }
        ],
        "malformed_rows": [],
    }
    shadow = {
        "records": [
            {
                "sample_id": "queued",
                "production_primary_track": "irrelevant",
                "production_secondary_tracks": [],
                "shadow_primary_track": MODULE.TRACKS[0],
                "shadow_secondary_tracks": [],
                "disagreement_category": "production_unlabeled_shadow_labeled",
            }
        ]
    }

    result = MODULE.evaluate(adjudicated, shadow)
    MODULE.write_outputs(result, tmp_path)

    assert result["human_gold_metrics_available"] is False
    assert result["shadow_vs_human_gold"] is None
    assert result["production_vs_human_gold"] is None
    assert result["review_queue_count"] == 1
    summary = (tmp_path / "v0.5_human_gold_metrics_v0.1.md").read_text(encoding="utf-8")
    assert "No final precision, recall, or F1 is computed" in summary
