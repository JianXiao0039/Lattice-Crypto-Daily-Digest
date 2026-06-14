from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/calculate_v0_5_human_gold_shadow_metrics.py"
SPEC = importlib.util.spec_from_file_location("v0_5_gold_validation", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_filled_label_without_user_status_is_invalid_and_not_gold() -> None:
    adjudicated = {
        "records": [
            {
                "sample_id": "not-user-confirmed",
                "human_review_status": "queued_for_user",
                "human_gold_primary_track": MODULE.TRACKS[0],
                "human_gold_secondary_tracks": [],
                "valid_human_gold": False,
            }
        ],
        "malformed_rows": [],
    }

    result = MODULE.evaluate(adjudicated, {"records": []})

    assert result["human_gold_count"] == 0
    assert result["invalid_annotation_count"] == 1
    assert result["human_gold_metric_status"] == "invalid_human_gold_annotations"


def test_user_confirmed_row_requires_primary_label() -> None:
    adjudicated = {
        "records": [
            {
                "sample_id": "missing-primary",
                "human_review_status": "user_confirmed",
                "human_gold_primary_track": None,
                "human_gold_secondary_tracks": [],
                "valid_human_gold": False,
            }
        ],
        "malformed_rows": [],
    }

    result = MODULE.evaluate(adjudicated, {"records": []})

    assert result["human_gold_count"] == 0
    assert result["invalid_annotation_count"] == 1


def test_adjudicator_accepts_explicit_multi_track_with_two_tracks() -> None:
    adjudicator = MODULE._load_adjudicator()
    errors: list[dict[str, str]] = []
    source = {
        "sample_id": "multi",
        "repository_record_id": "record-multi",
        "title": "Multi-track paper",
    }
    annotation = {
        "human_review_status": "user_confirmed",
        "human_gold_primary_track": "multi_track",
        "human_gold_secondary_tracks": MODULE.json.dumps(list(MODULE.TRACKS[:2])),
        "reviewer_note": "explicit user decision",
    }

    decision = adjudicator._validate_decision(source, annotation, errors)

    assert errors == []
    assert decision["valid_gold"] is True
    assert decision["primary"] == "multi_track"
    assert decision["secondary"] == list(MODULE.TRACKS[:2])
