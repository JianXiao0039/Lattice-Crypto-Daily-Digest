from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DEPLOYMENT_DOC = ROOT / "docs" / "deployment-public.md"
ENV_EXAMPLE = ROOT / ".env.example"
CHECK_SCRIPT = ROOT / "scripts" / "check_deployment.ps1"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_links_public_deployment_guide() -> None:
    readme = _read(README)

    assert "docs/deployment-public.md" in readme
    assert "快速部署" in readme or "Quick Deployment" in readme
    assert "不需要 Codex" in readme or "Codex is not required" in readme


def test_public_deployment_doc_covers_required_topics() -> None:
    doc = _read(DEPLOYMENT_DOC)

    for text in [
        "Windows 本地部署",
        "GitHub Actions",
        "本地权威回填",
        "Semantic Scholar",
        "SEMANTIC_SCHOLAR_API_KEY",
        "不要提交 `.env`",
        "Set-Location is not recognized",
    ]:
        assert text in doc


def test_env_example_contains_only_placeholders_and_no_real_tokens() -> None:
    content = _read(ENV_EXAMPLE)

    for key in [
        "CONTACT_EMAIL=",
        "SEMANTIC_SCHOLAR_API_KEY=",
        "SMTP_HOST=",
        "SMTP_PORT=",
        "SMTP_USERNAME=",
        "SMTP_PASSWORD=",
        "DIGEST_EMAIL_FROM=",
        "DIGEST_EMAIL_TO=",
    ]:
        assert key in content
    for forbidden in ["ghp_", "github_pat_", "sk-", "xoxb-", "AKIA"]:
        assert forbidden not in content


def test_check_deployment_script_exists_and_checks_core_tools() -> None:
    content = _read(CHECK_SCRIPT)

    assert "SEMANTIC_SCHOLAR_API_KEY" in content
    assert "Python" in content
    assert "git" in content
    assert "exit" in content


def test_public_docs_do_not_contain_common_secret_prefixes() -> None:
    combined = "\n".join(
        [
            _read(README),
            _read(DEPLOYMENT_DOC),
            _read(ENV_EXAMPLE),
        ]
    )

    for forbidden in ["ghp_", "github_pat_", "sk-", "xoxb-", "AKIA"]:
        assert forbidden not in combined
