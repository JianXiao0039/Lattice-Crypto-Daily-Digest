from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_v0_5_track_precision.py"
SPEC = importlib.util.spec_from_file_location("v0_5_track_precision", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
try:
    SPEC.loader.exec_module(MODULE)
except Exception:
    sys.modules.pop(SPEC.name, None)
    raise


def _record(paper_id: str, title: str, abstract: str) -> dict[str, object]:
    return {
        "paper_id": paper_id,
        "title": title,
        "abstract": abstract,
        "source": "fixture",
        "publication_date": "2026-06-12",
        "taxonomy_tags": [],
        "keywords_matched": [],
    }


def test_build_sample_is_repository_grounded_and_does_not_create_human_gold(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "2026-06-12.json").write_text(
        json.dumps(
            {
                "records": [
                    _record("fixture:a", "Module-SIS commitment", "A lattice commitment with a trapdoor."),
                    _record("fixture:b", "Falcon time-series model", "A generic forecasting model."),
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = MODULE.build_sample(tmp_path)

    assert payload["production_logic_changed"] is False
    assert payload["sample_size"] == 2
    assert payload["human_gold_count"] == 0
    assert all(row["human_review_status"] == "needs_user_review" for row in payload["records"])
    assert all(row["human_gold_primary_track"] is None for row in payload["records"])
    assert payload["records"][0]["source_provenance"] == ["data/2026-06-12.json"]


def test_machine_proposal_requires_evidence_beyond_title_storage() -> None:
    record = _record("fixture:c", "Generic registration system", "No cryptographic or lattice evidence.")
    primary, secondary, matches = MODULE.machine_proposal(record)
    assert primary is None
    assert secondary == []
    assert matches == {}


def test_human_gold_metrics_are_unavailable_without_user_review(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "2026-06-12.json").write_text(
        json.dumps({"records": [_record("fixture:d", "ML-KEM implementation", "An ML-KEM implementation study.")]}),
        encoding="utf-8",
    )
    payload = MODULE.build_sample(tmp_path)
    result = MODULE.evaluate_sample(payload)

    assert result["human_gold_metrics"]["valid_gold_count"] == 0
    assert result["human_gold_metrics"]["macro_f1"] is None
    assert result["annotation_coverage"] == 0.0


def test_default_evaluation_uses_frozen_sample_without_refreshing_repository_records() -> None:
    frozen = MODULE.load_frozen_sample()

    assert frozen["sample_size"] == len(frozen["records"])
    assert frozen["sample_size"] >= frozen["minimum_acceptable_size"]


def test_only_confirmed_or_corrected_rows_count_as_gold(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "2026-06-12.json").write_text(
        json.dumps({"records": [_record("fixture:e", "ML-DSA implementation", "An ML-DSA implementation study.")]}),
        encoding="utf-8",
    )
    payload = MODULE.build_sample(tmp_path)
    row = payload["records"][0]
    row["human_gold_primary_track"] = MODULE.TRACKS[3]
    row["human_review_status"] = "not_reviewed"
    assert MODULE.evaluate_sample(payload)["human_gold_metrics"]["valid_gold_count"] == 0

    row["human_review_status"] = "user_confirmed"
    assert MODULE.evaluate_sample(payload)["human_gold_metrics"]["valid_gold_count"] == 1


def test_output_writer_stays_inside_experimental_docs_namespace(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    source_path = tmp_path / "data" / "2026-06-12.json"
    original = json.dumps({"records": [_record("fixture:f", "Lattice dual attack", "A dual attack on LWE.")]})
    source_path.write_text(original, encoding="utf-8")
    payload = MODULE.build_sample(tmp_path)
    result = MODULE.evaluate_sample(payload)
    MODULE.write_outputs(payload, result, tmp_path)

    assert (tmp_path / "docs" / "research_tracks" / "v0.5_manual_precision_sample_v0.2.json").exists()
    assert source_path.read_text(encoding="utf-8") == original
    assert not (tmp_path / "digests").exists()
    assert not (tmp_path / "src").exists()


def test_repository_sample_meets_minimum_and_required_schema() -> None:
    payload = MODULE.load_frozen_sample()
    required = {
        "sample_id",
        "repository_record_id",
        "title",
        "source",
        "publication_date",
        "available_evidence",
        "machine_proposed_primary_track",
        "machine_proposed_secondary_tracks",
        "codex_reviewed_primary_track",
        "codex_reviewed_secondary_tracks",
        "human_gold_primary_track",
        "human_gold_secondary_tracks",
        "human_review_status",
        "relevance_status",
        "positive_evidence",
        "exclusion_evidence",
        "ambiguity_reason",
        "explanation",
        "source_provenance",
        "TODO_VERIFY",
    }
    assert payload["sample_size"] >= payload["minimum_acceptable_size"]
    assert len({row["sample_id"] for row in payload["records"]}) == payload["sample_size"]
    assert len({row["repository_record_id"] for row in payload["records"]}) == payload["sample_size"]
    assert all(required <= row.keys() for row in payload["records"])
    assert all(row["human_review_status"] in MODULE.VALID_REVIEW_STATUS for row in payload["records"])
    assert all(row["relevance_status"] in MODULE.VALID_RELEVANCE for row in payload["records"])


def test_generic_privacy_fhe_record_is_not_promoted_to_xingye_bridge(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "2026-06-12.json").write_text(
        json.dumps(
            {
                "records": [
                    _record(
                        "fixture:g",
                        "Privacy-preserving analytics with fully homomorphic encryption",
                        "An anonymous computation application using FHE.",
                    )
                ]
            }
        ),
        encoding="utf-8",
    )
    row = MODULE.build_sample(tmp_path)["records"][0]
    assert row["machine_proposed_primary_track"] == MODULE.TRACKS[1]
    assert row["codex_reviewed_primary_track"] == MODULE.TRACKS[3]
