from __future__ import annotations

from pathlib import Path

from lattice_digest.reliability_dashboard import build_reliability_baseline


def test_reliability_baseline_contains_required_fields(tmp_path: Path) -> None:
    root = tmp_path
    (root / "data").mkdir(parents=True)
    (root / "digests").mkdir(parents=True)
    (root / "data" / "weekly").mkdir(parents=True)
    (root / "handoffs" / "weekly").mkdir(parents=True)

    (root / "data" / "2026-06-08.json").write_text(
        '{"metadata":{"total_records":1},"records":[{"title":"x","relevance_label":"A"}],"source_health":[{"source":"arxiv","status":"green","retryable":false},{"source":"iacr_eprint","status":"yellow","latest_feed_status":"fetched","latest_feed_records":100},{"source":"semantic_scholar","status":"yellow","api_key_used":true}]}',
        encoding="utf-8",
    )
    (root / "digests" / "2026-06-08.md").write_text("# digest\n", encoding="utf-8")
    (root / "data" / "weekly" / "2026-W23.json").write_text('{"coverage":{"missing_days":[]}}', encoding="utf-8")
    (root / "handoffs" / "weekly" / "2026-W23-handoff-packets.json").write_text(
        '{"packets":[{"id":1}],"excluded":[],"todo_verify":[],"source_health_summary":{"status_counts":{"green":1,"yellow":1,"red":0}}}',
        encoding="utf-8",
    )

    payload = build_reliability_baseline(
        project_root=root,
        probe_payload=None,
        env={"SEMANTIC_SCHOLAR_API_KEY": "x" * 44},
    )

    required = {
        "baseline_date",
        "python_version",
        "package_version",
        "active_automation_modules",
        "paused_automation_modules",
        "latest_daily_artifact",
        "latest_weekly_artifact",
        "latest_handoff_artifact",
        "source_total_count",
        "source_green_count",
        "source_yellow_count",
        "source_red_count",
        "source_reachability_rate",
        "retryable_error_count",
        "digest_record_count",
        "final_record_count",
        "high_priority_count",
        "iacr_latest_status",
        "iacr_latest_records",
        "semantic_scholar_key_present_boolean",
        "semantic_scholar_key_length_only_if_safe",
        "semantic_scholar_enrichment_status",
        "source_starved_true_false",
        "empty_digest_reason",
        "weekly_handoff_candidate_count",
        "weekly_handoff_source_starved_true_false",
        "validation_passed",
        "manual_recovery_needed",
        "TODO_VERIFY",
    }
    assert required.issubset(payload)
    assert payload["latest_daily_artifact"] == "data/2026-06-08.json"
    assert payload["latest_weekly_artifact"] == "data/weekly/2026-W23.json"
    assert payload["latest_handoff_artifact"] == "handoffs/weekly/2026-W23-handoff-packets.json"
    assert all(
        "\\" not in payload[field]
        for field in ("latest_daily_artifact", "latest_weekly_artifact", "latest_handoff_artifact")
    )
    assert payload["active_automation_modules"] == ["Daily Public Digest Run", "Weekly Public Synthesis Run"]
    assert payload["paused_automation_modules"] == ["Full Manual Quality Run"]
    assert payload["source_reachability_rate"] == 1.0


def test_reliability_baseline_missing_artifacts_remain_none(tmp_path: Path) -> None:
    payload = build_reliability_baseline(project_root=tmp_path, env={})

    assert payload["latest_daily_artifact"] is None
    assert payload["latest_weekly_artifact"] is None
    assert payload["latest_handoff_artifact"] is None
