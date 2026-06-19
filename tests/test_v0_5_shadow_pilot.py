from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_v0_5_shadow_pilot.py"
SPEC = importlib.util.spec_from_file_location("v0_5_shadow_pilot", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
try:
    SPEC.loader.exec_module(MODULE)
except Exception:
    sys.modules.pop(SPEC.name, None)
    raise


def test_repository_pilot_completes_without_gold_metrics() -> None:
    sample = MODULE.SAMPLE.build_sample(ROOT)
    adjudicated = MODULE._load_json(MODULE.DEFAULT_ADJUDICATED)
    rules = MODULE._load_json(MODULE.DEFAULT_RULES)
    payload = MODULE.run_pilot(sample, adjudicated, rules)
    assert payload["broader_candidate_pool_count"] == len(sample["records"])
    assert payload["human_gold_count"] == 0
    assert payload["human_gold_metrics"]["eligible"] is False
    assert payload["shadow_pilot_status"] == "shadow_pilot_complete_without_gold_metrics"


def test_pilot_reports_only_non_gold_diagnostics_without_user_labels() -> None:
    sample = MODULE.SAMPLE.build_sample(ROOT)
    payload = MODULE.run_pilot(
        sample,
        MODULE._load_json(MODULE.DEFAULT_ADJUDICATED),
        MODULE._load_json(MODULE.DEFAULT_RULES),
    )
    assert (
        payload["production_shadow_agreement_count"]
        + payload["production_shadow_disagreement_count"]
        == len(sample["records"])
    )
    assert payload["human_gold_metrics"]["macro_f1"] is None
    assert payload["explanation_completeness_rate"] == 1.0


def test_pilot_writes_only_to_explicit_output_directory(tmp_path: Path) -> None:
    payload = MODULE.run_pilot(
        MODULE.SAMPLE.build_sample(ROOT),
        MODULE._load_json(MODULE.DEFAULT_ADJUDICATED),
        MODULE._load_json(MODULE.DEFAULT_RULES),
    )
    paths = MODULE.write_outputs(payload, tmp_path / "pilot")
    assert len(paths) == 9
    assert all(path.is_file() for path in paths)
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "digests").exists()
    assert not (tmp_path / "handoffs").exists()


def test_predictions_are_traceable_to_repository_provenance() -> None:
    payload = MODULE.run_pilot(
        MODULE.SAMPLE.build_sample(ROOT),
        MODULE._load_json(MODULE.DEFAULT_ADJUDICATED),
        MODULE._load_json(MODULE.DEFAULT_RULES),
    )
    assert all(row["record_id"] and row["source_provenance"] for row in payload["records"])
    assert all("available_evidence" in row for row in payload["records"])
    assert all(row["production_detail"] for row in payload["records"])
