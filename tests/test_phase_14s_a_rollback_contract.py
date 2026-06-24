from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rollback_plan_is_complete_and_non_destructive():
    text = (
        ROOT / "docs" / "operations" / "canonical_only_default_switch_rollback_v0.1.md"
    ).read_text(encoding="utf-8")

    assert "unset variable permits fallback" in text
    assert "unset variable disables fallback" in text
    assert "LATTICE_DIGEST_ALLOW_LEGACY_FALLBACK=1" in text
    assert "No artifact path changes" in text
    assert "No Git tracking changes" in text
    for forbidden in ("git add", "git commit", "git push", "git tag", "git rm", "git reset", "git clean"):
        assert forbidden not in text


def test_phase_14s_a_reports_do_not_claim_archive_or_release():
    report = (ROOT / "docs" / "reports" / "phase-14s-a-final-decision.md").read_text(
        encoding="utf-8"
    )
    assert "production_ready" not in report
    assert "legacy_artifacts_archived" not in report
    assert "No legacy artifact was copied, moved, archived, deleted, renamed, or pruned" in report
