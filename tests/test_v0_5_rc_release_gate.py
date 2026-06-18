from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKS = ROOT / "docs" / "research_tracks"


def test_v0_5_rc_gate_requires_ci_and_durable_evidence():
    status = (TRACKS / "release_gate_cleanup_v0.5_rc_status_v0.1.md").read_text(encoding="utf-8")
    blockers = (TRACKS / "release_gate_blocker_matrix_v0.1.md").read_text(encoding="utf-8")
    durable = (TRACKS / "release_gate_durable_evidence_status_v0.1.md").read_text(encoding="utf-8")
    assert "`v0_5_rc_ready_with_limits`" in status
    assert "Final release still requires CI evidence" in status
    assert "`blocked_until_ci_green`" in blockers
    assert "`durable_evidence_ready`" in durable


def test_v0_5_rc_docs_do_not_claim_production_ready():
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in TRACKS.glob("release_gate_*.md"))
    assert "production-ready" in combined
    assert "not final release" in combined or "not production-ready" in combined
    assert "production_ready" not in combined


def test_v0_5_rc_docs_exclude_manual_annotation_and_background_automation():
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in TRACKS.glob("release_gate_*.md"))
    assert "manual annotation dependency" in combined
    assert "absent" in combined
    assert "background automation" in combined
    assert "absent" in combined
