from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_seven_day_source_reliability.py"
SPEC = importlib.util.spec_from_file_location("seven_day_audit", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_daily(
    root: Path,
    day: str,
    records: list[dict],
    source_health: list[dict],
    *,
    markdown: bool = True,
) -> Path:
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "digests").mkdir(parents=True, exist_ok=True)
    path = root / "data" / f"{day}.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"target_date": day, "total_records": len(records)},
                "records": records,
                "source_health": source_health,
            }
        ),
        encoding="utf-8",
    )
    if markdown:
        (root / "digests" / f"{day}.md").write_text("# digest\n", encoding="utf-8")
    return path


def test_audit_classifies_pre_tag_source_starved_run(tmp_path: Path) -> None:
    health = [
        {"source": "iacr_eprint", "status": "red", "retryable": True, "latest_feed_status": "failed"},
        {
            "source": "semantic_scholar",
            "status": "red",
            "retryable": True,
            "api_key_used": True,
            "error_type": "warning",
            "error_message": "request error URLError",
        },
    ]
    path = write_daily(tmp_path, "2026-06-10", [], health)

    row = MODULE.audit_daily(tmp_path, path, date(2026, 6, 11))

    assert row["artifact_origin"] == "pre_tag_baseline"
    assert row["source_starved"] is True
    assert row["empty_digest_reason"] == "all_red_sources"
    assert row["semantic_scholar_status"] == "network_failure"
    assert row["semantic_scholar_key_present_boolean"] is True


def test_summary_requires_actual_post_tag_evidence() -> None:
    rows = [
        {
            "artifact_origin": "pre_tag_baseline",
            "markdown_exists": True,
            "json_exists": True,
            "source_total": 6,
            "source_green": 1,
            "source_yellow": 4,
            "source_red": 1,
            "source_starved": False,
            "retryable_error_count": 1,
            "non_retryable_error_count": 0,
            "iacr_latest_status": "fetched",
            "semantic_scholar_enrichment_available": False,
        }
    ]

    summary = MODULE.summarize(rows)

    assert summary["reliability_verdict"] == "insufficient_evidence"
    assert summary["v0_5_transition_decision"] == "insufficient_evidence"
    assert summary["post_tag_run_count"] == 0


def test_list_root_is_supported(tmp_path: Path) -> None:
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps([{"title": "legacy"}]), encoding="utf-8")

    payload = MODULE.load_daily(path)

    assert payload["records"] == [{"title": "legacy"}]
    assert payload["source_health"] == []
