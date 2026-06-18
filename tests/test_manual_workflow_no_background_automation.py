from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "docs" / "operations"


def _operation_docs() -> list[Path]:
    return sorted(OPS.glob("*.md"))


def test_runbooks_do_not_instruct_automatic_git_writes():
    forbidden_command_prefixes = (
        "git add ",
        "git commit",
        "git push",
        "git tag",
    )
    offending = []
    for path in _operation_docs():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip().lower()
            if stripped.startswith(forbidden_command_prefixes):
                offending.append(f"{path.name}:{line_number}:{line}")
    assert offending == []


def test_runbooks_do_not_create_background_automation():
    forbidden_phrases = [
        "schtasks /create",
        "new-scheduledtask",
        "crontab -e",
        "systemctl enable",
        "start-process",
        "register-scheduledtask",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in _operation_docs())
    for phrase in forbidden_phrases:
        assert phrase not in combined
    assert "automatic future run" in combined
    assert "manual-only" in combined


def test_runbooks_do_not_recommend_anti_bot_bypass():
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in _operation_docs())
    forbidden_actions = [
        "proxy rotation to evade",
        "fake user-agent rotation",
        "captcha bypass",
        "hidden browser automation to bypass",
        "ignoring source terms",
    ]
    for action in forbidden_actions:
        assert action in combined
    assert "forbidden" in combined
