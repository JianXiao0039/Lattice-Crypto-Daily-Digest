from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKS = ROOT / "docs" / "research_tracks"
REPORTS = ROOT / "docs" / "reports"


REQUIRED_TRACK_DOCS = [
    "release_gate_cleanup_v0.4.1_status_v0.1.md",
    "release_gate_cleanup_v0.5_rc_status_v0.1.md",
    "release_gate_ci_status_v0.1.md",
    "release_gate_durable_evidence_status_v0.1.md",
    "release_gate_source_health_status_v0.1.md",
    "release_gate_release_notes_cleanup_v0.1.md",
    "release_gate_blocker_matrix_v0.1.md",
    "release_gate_next_actions_v0.1.md",
    "release_gate_non_goals_v0.1.md",
]

REQUIRED_REPORTS = [
    "phase-13p-v0.4.1-v0.5-release-gate-cleanup.md",
    "phase-13p-v0.4.1-tag-audit.md",
    "phase-13p-v0.5-rc-gate-audit.md",
    "phase-13p-ci-and-release-hygiene-log.md",
    "phase-13p-durable-evidence-audit.md",
    "phase-13p-paper-radar-core-invariant-audit.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_release_gate_docs_exist():
    missing = [name for name in REQUIRED_TRACK_DOCS if not (TRACKS / name).exists()]
    missing += [name for name in REQUIRED_REPORTS if not (REPORTS / name).exists()]
    assert missing == []


def test_release_gate_docs_do_not_instruct_tag_deletion_or_recreation():
    combined = "\n".join(_read(TRACKS / name).lower() for name in REQUIRED_TRACK_DOCS)
    forbidden = [
        "git tag -d",
        "git push --delete",
        "recreate `v0.4.1`",
        "move `v0.4.1`",
    ]
    for phrase in forbidden:
        assert phrase not in combined
    assert "do not delete, move, recreate, or force-update" in combined


def test_release_gate_docs_do_not_instruct_automatic_git_writes():
    combined = "\n".join(_read(TRACKS / name).lower() for name in REQUIRED_TRACK_DOCS)
    assert "do not run `git add`" in combined
    assert "do not run `git commit`" in combined
    assert "do not run `git push`" in combined
    assert "do not run `git tag`" in combined
