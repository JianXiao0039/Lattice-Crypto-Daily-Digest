from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "experiments/v0_5_shadow_track_rules_v0.2.json"


def test_v02_rules_are_explicitly_experimental_and_field_aware() -> None:
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    policy = rules["evidence_policy"]
    assert rules["status"] == "candidate_not_promoted"
    assert rules["experimental_only"] is True
    assert rules["production_consumption_allowed"] is False
    assert policy["support_only_can_create_track"] is False
    assert policy["author_names_are_positive_features"] is False
    assert policy["prior_labels_are_features"] is False


def test_v02_rules_are_not_imported_by_production_or_workflows() -> None:
    forbidden = ("v0_5_shadow_track_rules_v0.2", "review_v0_5_shadow_errors")
    paths = list((ROOT / "src/lattice_digest").rglob("*.py"))
    paths += list((ROOT / ".github/workflows").glob("*.yml"))
    paths += list((ROOT / ".github/workflows").glob("*.yaml"))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not any(name in text for name in forbidden), path


def test_existing_shadow_pilot_does_not_silently_promote_v02() -> None:
    pilot = (ROOT / "scripts/run_v0_5_shadow_pilot.py").read_text(encoding="utf-8")
    classifier = (ROOT / "scripts/run_v0_5_shadow_track_classifier.py").read_text(encoding="utf-8")
    assert "v0_5_shadow_track_rules_v0.2" not in pilot
    assert "v0_5_shadow_track_rules_v0.2" not in classifier
    assert 'DEFAULT_RULES = PROJECT_ROOT / "experiments/v0_5_shadow_track_rules.json"' in pilot
