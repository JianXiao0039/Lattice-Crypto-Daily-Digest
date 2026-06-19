import json
from pathlib import Path

from scripts.audit_monthly_rationale_quality import build_audit
from tests.test_monthly_rationale_quality_audit import _write_fixture


FORBIDDEN_FIELDS = {
    "user_label",
    "human_gold_label",
    "user_confirmed",
    "user_corrected",
    "manual_annotation_status",
}


def test_audit_output_does_not_require_manual_annotation_fields(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    audit = build_audit(tmp_path, "2026-06")
    serialized = json.dumps(audit, ensure_ascii=False)

    for field in FORBIDDEN_FIELDS:
        assert field not in serialized


def test_audit_blocks_if_monthly_artifact_contains_user_annotation_dependency(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    monthly_path = tmp_path / "data" / "monthly" / "2026-06.json"
    payload = json.loads(monthly_path.read_text(encoding="utf-8"))
    payload["core_papers"][0]["human_gold_label"] = "module_sis_sanitizable_signatures"
    monthly_path.write_text(json.dumps(payload), encoding="utf-8")

    audit = build_audit(tmp_path, "2026-06")

    assert audit["pass_fail"] == "fail"
    assert "user annotation dependency" in audit["blockers"]
