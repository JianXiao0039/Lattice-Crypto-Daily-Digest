from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_v0_4_1_durable_daily_evidence.py"
SPEC = importlib.util.spec_from_file_location("verify_v041_durable", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_pair_detection_requires_both_markdown_and_json() -> None:
    paths = [
        "digests/2026-06-12.md",
        "data/2026-06-12.json",
        "digests/2026-06-13.md",
    ]
    pairs = MODULE._daily_pairs(paths, minimum_date=MODULE.date(2026, 6, 12))

    assert pairs[0]["pair_complete"] is True
    assert pairs[1]["pair_complete"] is False


def test_fake_origin_pair_is_not_enough_to_invent_automation_evidence() -> None:
    values = {
        ("rev-parse", "v0.4.0^{}"): MODULE.HISTORICAL_TARGET,
        ("rev-parse", "v0.4.1^{}"): "corrective-target",
        ("show", "-s", "--format=%cI", "v0.4.1^{}"): "2026-06-12T07:16:00+00:00",
        ("rev-parse", "HEAD"): "head",
        ("rev-parse", "origin/main"): "head",
        (
            "ls-tree",
            "-r",
            "--name-only",
            "origin/main",
        ): "digests/2026-06-13.md\ndata/2026-06-13.json",
        ("ls-files",): "digests/2026-06-13.md\ndata/2026-06-13.json",
    }

    report = MODULE.build_report(ROOT, git=lambda *args: values[args])

    assert report["origin_main_verification"] is True
    assert report["run_identifier"] is None
    assert report["ci_traceability"] is None
    assert report["evidence_class"] == "insufficient_evidence"
    assert report["durable_daily_evidence_exists"] is False
    assert "identifiable run" in report["TODO_VERIFY"][0]


def test_complete_tracked_manifest_can_establish_durable_evidence() -> None:
    manifest_path = (
        "docs/research_tracks/"
        "v0.4.1_durable_daily_evidence_manifest_2026-06-14.json"
    )
    manifest = {
        "evidence_class": "durable_automation_post_tag_actual",
        "run_identifier": "daily-2026-06-14",
        "target_date": "2026-06-14",
        "markdown_path": "digests/2026-06-14.md",
        "json_path": "data/2026-06-14.json",
        "source_health_summary": {"green": 5, "red": 1},
        "validation_result": "passed",
        "git_persistence": True,
        "origin_main_verification": True,
        "ci_traceability": "run-123",
    }
    values = {
        ("rev-parse", "v0.4.0^{}"): MODULE.HISTORICAL_TARGET,
        ("rev-parse", "v0.4.1^{}"): "corrective-target",
        ("show", "-s", "--format=%cI", "v0.4.1^{}"): "2026-06-12T07:16:00+00:00",
        ("rev-parse", "HEAD"): "head",
        ("rev-parse", "origin/main"): "head",
        (
            "ls-tree",
            "-r",
            "--name-only",
            "origin/main",
        ): f"digests/2026-06-14.md\ndata/2026-06-14.json\n{manifest_path}",
        ("ls-files",): "digests/2026-06-14.md\ndata/2026-06-14.json",
        ("show", f"origin/main:{manifest_path}"): MODULE.json.dumps(manifest),
    }

    report = MODULE.build_report(ROOT, git=lambda *args: values[args])

    assert report["evidence_class"] == "durable_automation_post_tag_actual"
    assert report["durable_daily_evidence_exists"] is True
