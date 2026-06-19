from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "docs" / "operations"
TRACKS = ROOT / "docs" / "research_tracks"


REQUIRED_SOURCE_DOCS = [
    "v0.6_source_health_long_run_stability_plan_v0.1.md",
    "v0.6_arxiv_rate_limit_long_run_policy_v0.1.md",
    "v0.6_dblp_tls_long_run_policy_v0.1.md",
    "v0.6_iacr_recovery_long_run_policy_v0.1.md",
    "v0.6_semantic_scholar_long_run_policy_v0.1.md",
    "v0.6_openalex_long_run_policy_v0.1.md",
    "v0.6_crossref_long_run_policy_v0.1.md",
    "v0.6_source_starved_interpretation_policy_v0.1.md",
]


def test_source_health_long_run_docs_exist() -> None:
    missing = [name for name in REQUIRED_SOURCE_DOCS if not (TRACKS / name).exists()]
    assert missing == []


def test_source_health_policy_requires_classification_and_source_starved_reporting() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in [*(TRACKS / name for name in REQUIRED_SOURCE_DOCS), OPS / "source_health_failure_interpretation_table_v0.1.md"])
    for phrase in [
        "rate_limited",
        "ssl",
        "tls",
        "failed-attempt guard",
        "missing_key",
        "auth_failure",
        "empty response",
        "network failure",
        "query mismatch",
        "source-starved",
    ]:
        assert phrase in combined


def test_source_health_policy_forbids_anti_abuse_bypass() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in [OPS / "source_health_long_run_stability_sop_v0.1.md", TRACKS / "v0.6_arxiv_rate_limit_long_run_policy_v0.1.md"])
    for phrase in [
        "proxy rotation",
        "fake user-agent rotation",
        "captcha bypass",
        "hidden browser automation",
        "disabling ssl verification as a production default",
        "background retry loops",
    ]:
        assert phrase in combined
    assert "forbidden" in combined
