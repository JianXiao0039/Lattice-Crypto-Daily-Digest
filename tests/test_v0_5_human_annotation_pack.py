from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_v0_5_human_annotation_pack.py"
SPEC = importlib.util.spec_from_file_location("v0_5_annotation_pack", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _sample() -> dict[str, object]:
    return {
        "sample_size": 2,
        "records": [
            {
                "sample_id": "a",
                "repository_record_id": "repo:a",
                "title": "Module-SIS chameleon hash",
                "source": "fixture",
                "available_evidence": {"abstract": "lattice trapdoor", "taxonomy_tags": [], "keywords_matched": []},
                "codex_reviewed_primary_track": "module_sis_sanitizable_signatures",
                "codex_reviewed_secondary_tracks": [],
                "control_label": None,
                "positive_evidence": "Module-SIS and lattice trapdoor evidence.",
                "exclusion_evidence": "None recorded.",
                "TODO_VERIFY": ["user review required"],
            },
            {
                "sample_id": "b",
                "repository_record_id": "repo:b",
                "title": "Generic commitment",
                "source": "fixture",
                "available_evidence": {"abstract": "no lattice anchor", "taxonomy_tags": [], "keywords_matched": []},
                "codex_reviewed_primary_track": "ambiguous",
                "codex_reviewed_secondary_tracks": [],
                "control_label": "ambiguous",
                "positive_evidence": "Insufficient evidence.",
                "exclusion_evidence": "No lattice anchor.",
                "TODO_VERIFY": ["user review required"],
            },
        ],
    }


def test_pack_never_creates_human_gold_labels() -> None:
    rules = MODULE.SHADOW.load_json(ROOT / "experiments/v0_5_shadow_track_rules.json")
    sample = _sample()
    shadow = MODULE.SHADOW.classify_sample(sample, rules)
    pack = MODULE.build_pack(sample, shadow, pack_size=20)

    assert pack["annotation_pack_size"] == 2
    assert pack["queued_user_review_count"] == 2
    assert pack["user_confirmed_count"] == 0
    assert all(row["human_gold_primary_track"] is None for row in pack["records"])
    assert all(row["human_review_status"] == "queued_for_user" for row in pack["records"])


def test_pack_prioritizes_disagreement_and_low_confidence() -> None:
    rules = MODULE.SHADOW.load_json(ROOT / "experiments/v0_5_shadow_track_rules.json")
    sample = _sample()
    shadow = MODULE.SHADOW.classify_sample(sample, rules)
    pack = MODULE.build_pack(sample, shadow, pack_size=1)
    assert pack["records"][0]["disagreement_type"] != "exact_match"


def test_writers_create_reviewable_json_csv_and_markdown(tmp_path: Path) -> None:
    rules = MODULE.SHADOW.load_json(ROOT / "experiments/v0_5_shadow_track_rules.json")
    sample = _sample()
    pack = MODULE.build_pack(sample, MODULE.SHADOW.classify_sample(sample, rules), pack_size=2)
    json_path, csv_path, md_path = MODULE.write_pack(pack, tmp_path)

    assert json.loads(json_path.read_text(encoding="utf-8"))["user_confirmed_count"] == 0
    csv_bytes = csv_path.read_bytes()
    assert not csv_bytes.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in csv_bytes
    assert b"\r" not in csv_bytes
    assert csv_bytes.endswith(b"\n")
    assert not csv_bytes.endswith(b"\n\n")
    assert "human_gold_primary_track" in csv_bytes.decode("utf-8")
    assert "Human gold primary track" in md_path.read_text(encoding="utf-8")


def test_repository_pack_uses_phase_13b_records_and_expected_size() -> None:
    sample = MODULE.SHADOW.load_json(MODULE.DEFAULT_SAMPLE)
    rules = MODULE.SHADOW.load_json(MODULE.DEFAULT_RULES)
    pack = MODULE.build_pack(sample, MODULE.SHADOW.classify_sample(sample, rules), pack_size=25)
    assert pack["annotation_pack_size"] == 25
    assert pack["source_sample_size"] == sample["sample_size"]
    assert len({row["repository_record_id"] for row in pack["records"]}) == 25
