from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BAT_PATH = ROOT / "scripts" / "push_all_digest_outputs.bat"


def _bat_text() -> str:
    return BAT_PATH.read_text(encoding="utf-8")


def test_push_all_digest_outputs_bat_exists_and_pushes_only_outputs() -> None:
    assert BAT_PATH.exists()
    text = _bat_text()

    assert "Lattice Crypto Daily Digest - Push Local Outputs" in text
    assert "D:\\Code\\CodexProjects\\lattice-crypto-daily-digest" in text
    assert "git ls-remote https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git" in text
    assert "git branch --show-current" in text
    assert "git pull --rebase origin main" in text
    assert "git add digests data papers.db" in text
    assert "git commit -m \"daily lattice digest outputs\"" in text
    assert "git push origin main" in text
    assert "No local digest outputs to commit." in text


def test_push_all_digest_outputs_bat_does_not_run_generation_or_scheduler() -> None:
    text = _bat_text().lower()

    assert "python -m lattice_digest.run" not in text
    assert "pytest" not in text
    assert "watcher" not in text
    assert "schtasks" not in text


def test_push_all_digest_outputs_bat_does_not_stage_secrets_or_whole_repo() -> None:
    text = _bat_text().lower()

    assert "git add ." not in text
    assert "git add .env" not in text
    assert "git add --all" not in text
    assert "git add -a" not in text
    assert "ghp_" not in text
    assert "github_pat_" not in text
    assert "token=" not in text


def test_push_all_digest_outputs_bat_warns_on_network_failure() -> None:
    text = _bat_text()

    assert "Please check Clash / Git proxy / GitHub login status." in text
    assert "git config --global --get http.proxy" in text
    assert "git config --global --get https.proxy" in text
    assert "http://127.0.0.1:7897" in text
    assert "pause" in text
