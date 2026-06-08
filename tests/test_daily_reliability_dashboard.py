from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lattice_digest.reliability_dashboard import build_reliability_dashboard, main


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_reliability_dashboard_for_non_empty_daily_run() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "data" / "2026-06-08.json",
            {
                "metadata": {"total_records": 2},
                "records": [
                    {"title": "A", "relevance_label": "A"},
                    {"title": "B", "reading_priority": 1},
                ],
                "source_health": [
                    {"source": "arxiv", "status": "green", "retryable": False},
                    {
                        "source": "iacr_eprint",
                        "status": "yellow",
                        "retryable": False,
                        "latest_feed_status": "fetched",
                        "latest_feed_records": 100,
                    },
                    {"source": "semantic_scholar", "status": "yellow", "retryable": False, "api_key_used": True},
                ],
            },
        )
        (root / "digests").mkdir(parents=True, exist_ok=True)
        (root / "digests" / "2026-06-08.md").write_text("# digest\n", encoding="utf-8")
        _write_json(root / "data" / "weekly" / "2026-W23.json", {"coverage": {"missing_days": ["2026-06-07"]}})
        _write_json(
            root / "handoffs" / "weekly" / "2026-W23-handoff-packets.json",
            {
                "packets": [{"id": 1}, {"id": 2}],
                "excluded": [{"id": 3}],
                "todo_verify": ["verify paper"],
                "source_health_summary": {"status_counts": {"green": 1, "yellow": 1, "red": 0}},
            },
        )

        probe_payload = {
            "probes": [
                {"source": "arxiv", "reachable": True, "retryable": False},
                {
                    "source": "semantic_scholar",
                    "reachable": False,
                    "retryable": True,
                    "status_code": 429,
                    "error_type": "rate_limit",
                },
                {"source": "iacr_eprint", "reachable": True, "retryable": False},
            ]
        }

        dashboard = build_reliability_dashboard(
            project_root=root,
            probe_payload=probe_payload,
            env={"SEMANTIC_SCHOLAR_API_KEY": "x" * 44},
        )

        assert dashboard["digest_record_count"] == 2
        assert dashboard["final_record_count"] == 2
        assert dashboard["high_priority_count"] == 2
        assert dashboard["source_green_count"] == 1
        assert dashboard["source_yellow_count"] == 2
        assert dashboard["source_red_count"] == 0
        assert dashboard["source_reachability_rate"] == 0.667
        assert dashboard["iacr_latest_status"] == "fetched"
        assert dashboard["iacr_latest_records"] == 100
        assert dashboard["semantic_scholar_enrichment_status"] == "rate_limit"
        assert dashboard["source_starved_true_false"] is False
        assert dashboard["weekly_handoff_candidate_count"] == 2
        assert dashboard["generated_artifacts_present"] is True
        assert dashboard["manual_recovery_needed"] is False


def test_build_reliability_dashboard_marks_source_starved_when_all_red() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "data" / "2026-06-07.json",
            {
                "metadata": {"total_records": 0},
                "records": [],
                "source_health": [
                    {"source": "arxiv", "status": "red", "retryable": True},
                    {"source": "crossref", "status": "red", "retryable": True},
                ],
            },
        )
        _write_json(root / "data" / "weekly" / "2026-W23.json", {"coverage": {"missing_days": []}})
        _write_json(
            root / "handoffs" / "weekly" / "2026-W23-handoff-packets.json",
            {
                "packets": [],
                "excluded": [],
                "todo_verify": [],
                "source_health_summary": {"status_counts": {"green": 0, "yellow": 0, "red": 2}},
            },
        )

        probe_payload = {
            "probes": [
                {"source": "arxiv", "reachable": False, "retryable": True},
                {"source": "crossref", "reachable": False, "retryable": True},
            ]
        }

        dashboard = build_reliability_dashboard(
            project_root=root,
            probe_payload=probe_payload,
            env={"SEMANTIC_SCHOLAR_API_KEY": ""},
        )

        assert dashboard["digest_record_count"] == 0
        assert dashboard["source_starved_true_false"] is True
        assert dashboard["empty_digest_reason"] == "all_red_sources"
        assert dashboard["manual_recovery_needed"] is True
        assert dashboard["semantic_scholar_enrichment_status"] == "missing_key"
        assert dashboard["weekly_handoff_source_starved_true_false"] is True


def test_cli_runs_without_probe_and_without_network() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "data" / "2026-06-08.json",
            {"metadata": {}, "records": [], "source_health": []},
        )
        (root / "digests").mkdir(parents=True, exist_ok=True)
        (root / "digests" / "2026-06-08.md").write_text("# digest\n", encoding="utf-8")
        _write_json(root / "data" / "weekly" / "2026-W23.json", {"coverage": {}})
        _write_json(
            root / "handoffs" / "weekly" / "2026-W23-handoff-packets.json",
            {"packets": [], "excluded": [], "todo_verify": [], "source_health_summary": {"status_counts": {}}},
        )

        assert main(["--project-root", str(root), "--skip-probe", "--format", "json"]) == 0
