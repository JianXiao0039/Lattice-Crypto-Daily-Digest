from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_v0_5_rc import build_report


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_root(root: Path) -> None:
    for report in (
        "phase-13i-controlled-production-patch-proposal-for-v0.5.md",
        "phase-13j-daily-weekly-rationale-integration.md",
        "phase-13k-monthly-lattice-paper-radar-synthesis.md",
        "phase-13l-source-health-and-durable-artifact-recovery.md",
        "phase-13m-reading-queue-and-obsidian-export-polishing.md",
    ):
        _write(root / "docs/reports" / report, "# ok\n")
    for script in (
        "probe_source_health.py",
        "verify_durable_artifacts.py",
        "export_reading_queue.py",
        "export_obsidian_notes.py",
    ):
        _write(root / "scripts" / script, "# script\n")
    _write(
        root / "docs/research_tracks/v0.5_rc_bilingual_rationale_policy_v0.1.md",
        "中文\nEnglish\nA-class\ntop weekly\ntop monthly\n",
    )
    daily = {
        "metadata": {"target_date": "2026-06-15"},
        "records": [{"title": "LWE paper"}],
        "source_health": [
            {"source": "arxiv", "status": "yellow", "error_type": "rate_limit"},
            {"source": "semantic_scholar", "status": "yellow", "api_key_used": True},
            {"source": "openalex", "status": "green"},
            {"source": "iacr_eprint", "status": "green", "latest_feed_status": "normal_latest_feed_success"},
        ],
    }
    _write(root / "data/2026-06-15.json", json.dumps(daily))
    _write(root / "digests/2026-06-15.md", "# Daily\n\n数据源健康\nlattice/PQC anchor evidence\n")
    _write(root / "audits/source-health/2026-06-15.json", json.dumps({"sources": []}))
    weekly = {
        "generated_at": "2026-06-15T00:00:00+00:00",
        "coverage": {"input_dates": ["2026-06-15"]},
        "source_health_summary": {"available": True},
    }
    _write(root / "data/weekly/2026-W25.json", json.dumps(weekly))
    _write(root / "digests/weekly/2026-W25.md", "# Weekly\n\nlattice/PQC anchor evidence\n")
    monthly = {
        "month": "2026-06",
        "input_daily_files": ["data/2026-06-15.json"],
        "missing_days": [],
        "source_health_summary": {"source_starved": False},
    }
    _write(root / "data/monthly/2026-06.json", json.dumps(monthly))
    _write(root / "digests/monthly/2026-06.md", "# Monthly\n\nProblem\nMethod\nContribution\nEvidence basis\nTODO_VERIFY\n")
    queue = {
        "records": [
            {
                "title": "LWE paper",
                "reading_action": "精读",
                "rationale_problem": "Problem",
                "evidence_basis": ["abstract-derived"],
                "TODO_VERIFY": ["TODO_VERIFY"],
            }
        ]
    }
    _write(root / "state/reading-queue.json", json.dumps(queue, ensure_ascii=False))
    note = "\n".join(
        [
            "---",
            "status: unread",
            "---",
            "## 1. Radar Recommendation",
            "## 2. Paper Work Summary",
            "## 3. Relevance to My Research",
            "## 4. Reading Checklist",
            "## 5. TODO_VERIFY",
            "## 6. Links",
            "",
        ]
    )
    _write(root / "exports/obsidian-paper-notes/Papers/lwe-paper.md", note)
    _write(root / "exports/reading-queue/reading-dashboard.md", "# Reading Dashboard\n")


def test_v0_5_rc_verifier_passes_complete_fixture(tmp_path: Path) -> None:
    _fixture_root(tmp_path)

    report = build_report(tmp_path, target_date="2026-06-15", week="2026-W25", month="2026-06")

    assert report["v0_5_rc_decision"] == "v0_5_rc_ready_with_limits"
    assert report["durable_evidence"]["status"] == "durable_evidence_ready"
    assert report["reading_queue"]["manual_annotation_dependency"] is False
    assert report["obsidian_export"]["ok"] is True


def test_v0_5_rc_verifier_blocks_missing_bilingual_policy(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    (tmp_path / "docs/research_tracks/v0.5_rc_bilingual_rationale_policy_v0.1.md").unlink()

    report = build_report(tmp_path, target_date="2026-06-15", week="2026-W25", month="2026-06")

    assert "bilingual_policy_incomplete" in report["blockers"]
    assert report["v0_5_rc_decision"] == "v0_5_rc_blocked_by_multiple_conditions"
