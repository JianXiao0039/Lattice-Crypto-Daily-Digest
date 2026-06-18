from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKS = ROOT / "docs" / "research_tracks"
REPORTS = ROOT / "docs" / "reports"


def test_v0_4_1_blocked_status_is_not_mislabeled_as_released():
    status = (TRACKS / "release_gate_cleanup_v0.4.1_status_v0.1.md").read_text(encoding="utf-8")
    report = (REPORTS / "phase-13p-v0.4.1-tag-audit.md").read_text(encoding="utf-8")
    assert "`v0_4_1_tag_exists_blocked`" in status
    assert "`v0_4_1_tag_exists_blocked`" in report
    assert "historical blocked" in status.lower()
    assert "durable evidence" in status.lower()
    assert "missing" in status.lower()


def test_v0_4_1_target_commit_is_documented():
    status = (TRACKS / "release_gate_cleanup_v0.4.1_status_v0.1.md").read_text(encoding="utf-8")
    assert "95215b5afe18b1f13463d03929bfe27f15788695" in status
    assert "e092486203d39913affb1fa8ac97cd3dd03fc513" in status
    assert "does not point to HEAD" in status


def test_v0_4_1_release_notes_need_update_is_documented():
    notes = (TRACKS / "release_gate_release_notes_cleanup_v0.1.md").read_text(encoding="utf-8")
    assert "`release_notes_need_update`" in notes
    assert "tag now exists" in notes
    assert "Do not claim v0.4.1 is fully releasable" in notes
