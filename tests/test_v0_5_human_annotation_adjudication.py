from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/adjudicate_v0_5_human_annotations.py"
SPEC = importlib.util.spec_from_file_location("v0_5_adjudication", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _source() -> dict[str, object]:
    return {
        "records": [
            {
                "sample_id": "s1",
                "repository_record_id": "repo:1",
                "title": "Module-SIS chameleon hash",
                "current_production_primary_track": "module_sis_sanitizable_signatures",
                "shadow_proposed_primary_track": "module_sis_sanitizable_signatures",
            }
        ]
    }


def _annotation(**updates: str) -> dict[str, str]:
    row = {
        "sample_id": "s1",
        "repository_record_id": "repo:1",
        "title": "Module-SIS chameleon hash",
        "human_gold_primary_track": "",
        "human_gold_secondary_tracks": "[]",
        "human_review_status": "queued_for_user",
        "reviewer_note": "",
    }
    row.update(updates)
    return row


def test_unreviewed_row_remains_queued_and_not_gold() -> None:
    payload = MODULE.adjudicate(_source(), {"s1": _annotation()}, [])
    assert payload["annotation_status"] == "queued_for_user_review"
    assert payload["valid_human_gold_count"] == 0
    assert payload["records"][0]["human_gold_primary_track"] is None


def test_only_explicit_valid_user_status_creates_gold() -> None:
    row = _annotation(
        human_gold_primary_track="module_sis_sanitizable_signatures",
        human_review_status="user_confirmed",
        reviewer_note="Reviewed by user.",
    )
    payload = MODULE.adjudicate(_source(), {"s1": row}, [])
    assert payload["valid_human_gold_count"] == 1
    assert payload["gold_metrics_eligible"] is True
    assert payload["records"][0]["conflict_resolution"] == "all_agree"


def test_invalid_gold_state_is_blocked_and_not_inferred() -> None:
    payload = MODULE.adjudicate(_source(), {"s1": _annotation(human_review_status="user_confirmed")}, [])
    assert payload["annotation_status"] == "blocked_by_invalid_annotations"
    assert payload["valid_human_gold_count"] == 0
    assert payload["records"][0]["human_review_status"] == "conflict_requires_adjudication"


def test_csv_loader_preserves_explicit_decision_fields(tmp_path: Path) -> None:
    path = tmp_path / "annotations.csv"
    rows = [_annotation()]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    loaded, errors = MODULE.load_annotation_rows(path)
    assert errors == []
    assert loaded["s1"]["human_review_status"] == "queued_for_user"


def test_repository_annotation_pack_has_no_inferred_gold() -> None:
    rows, errors = MODULE.load_annotation_rows(MODULE.DEFAULT_ANNOTATIONS)
    payload = MODULE.adjudicate(MODULE._load_json(MODULE.DEFAULT_SOURCE_PACK), rows, errors)
    assert payload["annotation_rows_processed"] == 25
    assert payload["valid_human_gold_count"] == 0
    assert payload["queued_count"] == 25
    assert payload["malformed_rows"] == []
