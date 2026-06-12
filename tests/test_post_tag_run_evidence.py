from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "collect_post_tag_run_evidence.py"
SPEC = importlib.util.spec_from_file_location("post_tag_evidence", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_pre_tag_artifact_is_not_counted_as_post_tag(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "data").mkdir()
    path = tmp_path / "data" / "2026-06-10.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"run_date": "2026-06-10", "collector": "local_codex"},
                "records": [],
                "source_health": [{"source": "arxiv", "status": "red"}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(MODULE, "run_git", lambda *args: "abc123")

    rows = MODULE.artifact_evidence(tmp_path, "2026-06-11T01:05:06+08:00")

    assert rows[0]["evidence_class"] == "pre_tag_baseline"
    assert rows[0]["source_starved_status"] is True


def test_github_daily_run_after_tag_is_actual_evidence(monkeypatch) -> None:
    run_payload = {
        "workflow_runs": [
            {
                "id": 1,
                "name": "Daily Lattice Crypto Digest",
                "run_started_at": "2026-06-11T06:04:39Z",
                "conclusion": "failure",
                "head_sha": "abc",
                "jobs_url": "jobs",
                "html_url": "https://example.invalid/run/1",
            }
        ]
    }
    jobs_payload = {
        "jobs": [
            {
                "steps": [
                    {"name": "Run daily digest", "conclusion": "success"},
                    {"name": "Verify generated artifacts", "conclusion": "success"},
                    {"name": "Commit generated digest", "conclusion": "failure"},
                ]
            }
        ]
    }
    monkeypatch.setattr(MODULE, "fetch_json", lambda url: jobs_payload if url == "jobs" else run_payload)

    rows, warnings = MODULE.post_tag_workflow_evidence("2026-06-11T01:05:06+08:00")

    assert warnings == []
    assert rows[0]["evidence_class"] == "automation_post_tag_actual"
    assert rows[0]["validation_status"] == "generated_and_verified_ephemeral_commit_failed"


def test_evidence_taxonomy_is_exact() -> None:
    assert MODULE.EVIDENCE_CLASSES == {
        "automation_post_tag_actual",
        "manual_post_tag_equivalent",
        "pre_tag_baseline",
        "historical_ci_evidence",
        "synthetic_test_fixture",
        "unknown",
    }
