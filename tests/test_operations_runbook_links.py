from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "docs" / "operations"


REQUIRED_RUNBOOKS = [
    "radar_manual_operations_runbook_v0.1.md",
    "daily_radar_manual_runbook_v0.1.md",
    "weekly_radar_manual_runbook_v0.1.md",
    "monthly_radar_manual_runbook_v0.1.md",
    "full_radar_manual_runbook_v0.1.md",
    "backfill_specific_date_runbook_v0.1.md",
    "specific_time_range_runbook_v0.1.md",
    "source_health_manual_recovery_runbook_v0.1.md",
    "durable_artifact_verification_runbook_v0.1.md",
    "reading_queue_obsidian_export_runbook_v0.1.md",
    "operator_handoff_template_v0.1.md",
    "codex_operator_policy_v0.1.md",
    "deepseek_claude_operator_policy_v0.1.md",
    "kimi_code_operator_policy_v0.1.md",
    "anti_abuse_low_load_policy_v0.1.md",
    "no_background_automation_policy_v0.1.md",
]


def _read(name: str) -> str:
    return (OPS / name).read_text(encoding="utf-8")


def test_required_operations_runbooks_exist():
    missing = [name for name in REQUIRED_RUNBOOKS if not (OPS / name).exists()]
    assert missing == []


def test_daily_weekly_monthly_commands_are_documented():
    combined = "\n".join(_read(name) for name in REQUIRED_RUNBOOKS)
    assert "python -m lattice_digest.run --since 36h" in combined
    assert "python -m lattice_digest.run --date YYYY-MM-DD" in combined
    assert "python -m lattice_digest.workflow weekly --low-load" in combined
    assert "python -m lattice_digest.monthly_synthesis --month YYYY-MM" in combined
    assert "python scripts\\verify_durable_artifacts.py" in combined
    assert "python scripts\\export_reading_queue.py --latest" in combined
    assert "python scripts\\export_obsidian_notes.py --latest" in combined


def test_backfill_and_time_range_procedures_are_documented():
    backfill = _read("backfill_specific_date_runbook_v0.1.md")
    time_range = _read("specific_time_range_runbook_v0.1.md")
    assert "--run-mode backfill" in backfill
    assert "--quality-status authoritative_backfill" in backfill
    assert "--since 7d" in time_range
    assert "does not expose `--start` / `--end`" in time_range
