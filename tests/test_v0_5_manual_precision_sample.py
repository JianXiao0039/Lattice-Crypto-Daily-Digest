from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_v0_5_manual_precision_sample.py"
SPEC = importlib.util.spec_from_file_location("precision_sample", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_sample_uses_existing_records_and_keeps_production_unchanged(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    selected = next(iter(MODULE.ANNOTATIONS))
    (tmp_path / "data" / "2026-06-10.json").write_text(
        json.dumps({"records": [{"paper_id": selected, "title": "Observed title", "source": "observed"}]}),
        encoding="utf-8",
    )
    original = MODULE.ANNOTATIONS
    try:
        MODULE.ANNOTATIONS = {selected: original[selected]}
        payload = MODULE.build_sample(tmp_path)
    finally:
        MODULE.ANNOTATIONS = original

    assert payload["sample_size"] == 1
    assert payload["records"][0]["title"] == "Observed title"
    assert payload["production_logic_changed"] is False


def test_sample_contains_positive_negative_and_ambiguous_annotations() -> None:
    labels = {item["relevant"] for item in MODULE.ANNOTATIONS.values()}
    assert labels == {"yes", "no", "ambiguous"}


def test_xingye_annotations_do_not_claim_professor_facts() -> None:
    for item in MODULE.ANNOTATIONS.values():
        if item["primary_track"] == "xingye_lu_bridge":
            text = " ".join(
                [item["positive_evidence"], item["exclusion_evidence"], item["annotator_note"]]
            ).lower()
            assert "authored by xingye" not in text
            assert "xingye lu works on" not in text
