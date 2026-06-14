from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_v0_5_shadow_mode_pilot.py"
SPEC = importlib.util.spec_from_file_location("v0_5_shadow_mode_pilot", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _payload() -> dict:
    return MODULE.build_controlled_pilot(
        MODULE.load_json(MODULE.DEFAULT_INPUT),
        MODULE.load_json(MODULE.DEFAULT_RULES),
        run_id="test-manual-run",
    )


def test_controlled_pilot_runs_and_writes_separate_audit_bundle() -> None:
    payload = _payload()
    shadow_root = ROOT / "audits/shadow"
    shadow_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=shadow_root) as directory:
        output = Path(directory) / "shadow"
        paths = MODULE.write_outputs(
            payload,
            output,
            snapshot_path=MODULE.DEFAULT_INPUT,
            rules_path=MODULE.DEFAULT_RULES,
        )

        assert payload["run_mode"] == "manual_only"
        assert payload["production_logic_changed"] is False
        assert payload["production_outputs_written"] is False
        assert payload["record_count"] > 0
        assert payload["human_gold_count"] == 0
        assert {path.name for path in paths} == {
            "manifest.json",
            "predictions.json",
            "disagreements.json",
            "summary.md",
        }
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["pilot_type"] == "controlled_shadow_non_production"


@pytest.mark.parametrize("relative", ["data/shadow", "digests/shadow", "handoffs/shadow", "src/shadow"])
def test_controlled_pilot_rejects_production_output_paths(relative: str) -> None:
    with pytest.raises(ValueError, match="production path"):
        MODULE.validate_output_directory(ROOT / relative)


def test_v02_support_only_evidence_cannot_create_track() -> None:
    record = {
        "title": "A generic systems paper",
        "available_evidence": {
            "abstract": "No cryptographic construction is studied.",
            "taxonomy_tags": ["ML-KEM", "lattice"],
            "keywords_matched": ["PQC"],
        },
    }
    prediction = MODULE.shadow_prediction(record, MODULE.load_json(MODULE.DEFAULT_RULES))
    assert prediction["primary"] == "irrelevant"
