from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "docs" / "operations"


DOCS = [
    "cross_operator_manual_workflow_parity_v0.1.md",
    "codex_deepseek_kimi_command_matrix_v0.1.md",
    "manual_full_run_sop_v0.1.md",
    "manual_specific_date_and_range_sop_v0.1.md",
    "source_health_long_run_stability_sop_v0.1.md",
    "operator_parity_no_release_owner_policy_v0.1.md",
]


def test_new_runbooks_do_not_create_background_automation() -> None:
    combined = "\n".join((OPS / name).read_text(encoding="utf-8").lower() for name in DOCS)
    forbidden_positive_commands = [
        "schtasks /create",
        "register-scheduledtask",
        "new-scheduledtask",
        "crontab -e",
        "systemctl enable",
        "nohup ",
    ]
    for command in forbidden_positive_commands:
        assert command not in combined
    assert "background service" in combined
    assert "automatic future run" in combined


def test_new_runbooks_do_not_instruct_automatic_git_or_tag_operations() -> None:
    lines = []
    for name in DOCS:
        path = OPS / name
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip().lower()
            if stripped.startswith(("git add ", "git commit", "git push ", "git tag ")):
                lines.append(f"{name}:{line_number}:{line}")
    assert lines == []
