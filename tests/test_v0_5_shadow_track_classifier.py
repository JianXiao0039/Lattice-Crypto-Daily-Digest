from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_v0_5_shadow_track_classifier.py"
SPEC = importlib.util.spec_from_file_location("v0_5_shadow", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _rules() -> dict[str, object]:
    return json.loads((ROOT / "experiments" / "v0_5_shadow_track_rules.json").read_text(encoding="utf-8"))


def _record(title: str, abstract: str = "") -> dict[str, object]:
    return {
        "sample_id": "fixture-1",
        "repository_record_id": "fixture:1",
        "title": title,
        "source": "fixture",
        "available_evidence": {"abstract": abstract, "taxonomy_tags": [], "keywords_matched": []},
        "positive_evidence": "",
        "exclusion_evidence": "",
    }


def test_shadow_requires_positive_term_and_lattice_anchor() -> None:
    generic = MODULE.shadow_prediction(_record("Generic commitment system"), _rules())
    anchored = MODULE.shadow_prediction(
        _record("Module-SIS chameleon hash", "A lattice trapdoor supports controlled collisions."), _rules()
    )

    assert generic["primary"] in {"irrelevant", "ambiguous"}
    assert anchored["primary"] == "module_sis_sanitizable_signatures"


def test_shadow_does_not_promote_generic_machine_learning() -> None:
    result = MODULE.shadow_prediction(
        _record("Transformer for time series", "A generic machine learning forecasting system."), _rules()
    )
    assert result["primary"] in {"irrelevant", "ambiguous"}


def test_shadow_does_not_consume_prior_annotation_explanations() -> None:
    record = _record("Generic registration system", "No cryptographic evidence.")
    record["positive_evidence"] = "Module-SIS lattice trapdoor chameleon hash"
    result = MODULE.shadow_prediction(record, _rules())
    assert result["primary"] in {"irrelevant", "ambiguous"}


def test_classification_preserves_human_review_boundary() -> None:
    payload = MODULE.classify_sample({"records": [_record("ML-KEM implementation")]}, _rules())
    row = payload["records"][0]
    assert payload["human_gold_count"] == 0
    assert row["human_review_status"] == "queued_for_user"
    assert row["shadow_primary_track"] == "core_pqc_and_implementation"


def test_output_is_written_only_to_explicit_experimental_directory(tmp_path: Path) -> None:
    payload = MODULE.classify_sample({"records": [_record("LWE dual attack")]}, _rules())
    json_path, md_path = MODULE.write_outputs(payload, tmp_path / "audits" / "shadow")

    assert json_path.exists()
    assert md_path.exists()
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "digests").exists()
    assert not (tmp_path / "handoffs").exists()


def test_repository_sample_produces_traceable_shadow_rows() -> None:
    sample = MODULE.load_json(ROOT / "docs" / "research_tracks" / "v0.5_manual_precision_sample_v0.2.json")
    payload = MODULE.classify_sample(sample, _rules())
    assert payload["record_count"] == sample["sample_size"]
    assert all(row["record_id"] and row["sample_id"] for row in payload["records"])
    assert all(row["disagreement_category"] for row in payload["records"])
