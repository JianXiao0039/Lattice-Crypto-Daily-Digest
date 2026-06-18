import json
from pathlib import Path

from scripts.audit_monthly_rationale_quality import build_audit, write_outputs
from tests.test_monthly_rationale_quality_audit import _write_fixture


def test_audit_output_is_deterministic_and_writes_reports(tmp_path: Path):
    _write_fixture(tmp_path)
    audit_a = build_audit(tmp_path, "2026-06")
    audit_b = build_audit(tmp_path, "2026-06")
    assert audit_a == audit_b
    write_outputs(audit_a, tmp_path, tmp_path / "reports", tmp_path / "tracks")
    assert (tmp_path / "reports" / "phase-13r-rationale-quality-scorecard.md").exists()
    assert (tmp_path / "tracks" / "v0.5_monthly_real_case_quality_audit_v0.1.md").exists()
    payload = json.loads((tmp_path / "reports" / "phase-13r-real-paper-case-audit-log.json").read_text(encoding="utf-8"))
    assert payload["month"] == "2026-06"


def test_missing_monthly_artifact_blocks_without_network(tmp_path: Path):
    audit = build_audit(tmp_path, "2026-06")
    assert audit["decision"] == "monthly_rationale_quality_blocked_by_missing_monthly_artifact"
    assert audit["sample"] == []
