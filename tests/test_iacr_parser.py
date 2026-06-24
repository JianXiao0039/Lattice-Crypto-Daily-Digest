from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import lattice_digest.run as run_module
import lattice_digest.sources.iacr as iacr_module
from lattice_digest.artifact_paths import daily_data_path
from lattice_digest.config import load_config_bundle
from lattice_digest.ranker import rank_records
from lattice_digest.sources.base import FetchContext
from lattice_digest.sources.iacr import parse_iacr_feed


def test_iacr_rss_parser_extracts_eprint_record() -> None:
    xml = """<?xml version="1.0"?>
    <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
      <channel>
        <item>
          <title>Improved Module-LWE Signatures</title>
          <link>https://eprint.iacr.org/2026/123</link>
          <description>We construct lattice-based signatures from Module-LWE.</description>
          <dc:creator>Alice Example</dc:creator>
          <pubDate>Fri, 22 May 2026 01:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    records = parse_iacr_feed(xml)

    assert len(records) == 1
    record = records[0]
    assert record.title == "Improved Module-LWE Signatures"
    assert record.authors == ["Alice Example"]
    assert record.eprint_id == "2026/123"
    assert record.pdf_url == "https://eprint.iacr.org/2026/123.pdf"
    assert record.source == "iacr_eprint"


def _sample_iacr_xml() -> str:
    return """<?xml version="1.0"?>
    <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
      <channel>
        <item>
          <title>On the Secrecy of the Encapsulation Coin in ML-KEM</title>
          <link>https://eprint.iacr.org/2026/1117</link>
          <description>We analyze ML-KEM encapsulation coin secrecy.</description>
          <dc:creator>Alice Example</dc:creator>
          <pubDate>Sun, 31 May 2026 01:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """


def _latest_iacr_xml() -> str:
    items = [
        (
            "The Fact of the MATTER: Efficient Hardware Accelerators for Wide-Block Memory Encryption",
            "2026/1115",
            "We study cryptographic hardware acceleration for memory encryption.",
        ),
        (
            "Fast Difficulty Adjustment in Proof-of-Work Consensus",
            "2026/1116",
            "We study proof-of-work consensus difficulty adjustment.",
        ),
        (
            "On the Secrecy of the Encapsulation Coin in ML-KEM",
            "2026/1117",
            "We analyze ML-KEM encapsulation coin secrecy for post-quantum KEM implementations.",
        ),
        (
            "AuditPay: Anonymous Payments with Controlled Oversight",
            "2026/1118",
            "We study anonymous payments with controlled oversight.",
        ),
    ]
    body = "\n".join(
        f"""
        <item>
          <title>{title}</title>
          <link>https://eprint.iacr.org/{eprint_id}</link>
          <description>{description}</description>
          <dc:creator>Alice Example</dc:creator>
          <pubDate>Sun, 31 May 2026 01:00:00 GMT</pubDate>
        </item>
        """
        for title, eprint_id, description in items
    )
    return f"""<?xml version="1.0"?>
    <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
      <channel>{body}</channel>
    </rss>
    """


def _context(
    tmp_path: Path,
    *,
    retry_failed_sources: bool = False,
    include_latest_sources: bool = False,
) -> FetchContext:
    return FetchContext(
        root=tmp_path,
        since=datetime(2026, 5, 30, tzinfo=timezone.utc),
        dry_run=False,
        cache_dir=tmp_path / "cache",
        retry_failed_sources=retry_failed_sources,
        include_latest_sources=include_latest_sources,
    )


def _source(*, expected_latest_ids: list[str] | None = None) -> iacr_module.IacrEprintSource:
    return iacr_module.IacrEprintSource(
        {
            "name": "iacr_eprint",
            "type": "iacr_eprint",
            "url": "https://eprint.iacr.org/rss/rss.xml",
            "expected_latest_ids": expected_latest_ids or [],
        }
    )


def test_iacr_successful_fetch_is_still_guarded_by_cache(tmp_path: Path, monkeypatch) -> None:
    calls = 0

    def fake_fetch_text(context, url, source_name):  # noqa: ANN001
        nonlocal calls
        calls += 1
        return _sample_iacr_xml()

    monkeypatch.setattr(iacr_module, "fetch_text", fake_fetch_text)

    first_records = _source().fetch(_context(tmp_path))
    assert calls == 1
    assert first_records[0].eprint_id == "2026/1117"

    def fail_if_called(context, url, source_name):  # noqa: ANN001
        raise AssertionError("successful IACR cache should guard later same-day fetches")

    monkeypatch.setattr(iacr_module, "fetch_text", fail_if_called)
    second_records = _source().fetch(_context(tmp_path))

    assert calls == 1
    assert second_records[0].eprint_id == "2026/1117"


def test_iacr_failed_attempt_requires_manual_retry_to_fetch_again(tmp_path: Path, monkeypatch) -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / f"iacr_eprint_{today}.attempt").write_text("failed earlier", encoding="utf-8")

    def fail_if_called(context, url, source_name):  # noqa: ANN001
        raise AssertionError("failed IACR attempt should not retry without explicit manual flag")

    monkeypatch.setattr(iacr_module, "fetch_text", fail_if_called)
    skipped_context = _context(tmp_path)
    assert _source().fetch(skipped_context) == []
    skipped_health = skipped_context.source_health_summary()[0]
    assert skipped_health["status"] == "red"
    assert "already requested today" in str(skipped_health["warnings"][0])

    def recovered_fetch_text(context, url, source_name):  # noqa: ANN001
        return _sample_iacr_xml()

    monkeypatch.setattr(iacr_module, "fetch_text", recovered_fetch_text)
    retry_context = _context(tmp_path, retry_failed_sources=True)
    recovered_records = _source().fetch(retry_context)
    recovered_health = retry_context.source_health_summary()[0]

    assert recovered_records[0].eprint_id == "2026/1117"
    assert recovered_health["raw_count"] == 1
    assert recovered_health["date_filtered_count"] == 1
    assert "manual retry enabled" in str(recovered_health["warnings"][0])


def test_iacr_latest_feed_parser_discovers_phase_9s2_sample_ids() -> None:
    records = parse_iacr_feed(_latest_iacr_xml())
    by_id = {record.eprint_id: record for record in records}

    assert set(by_id) == {"2026/1115", "2026/1116", "2026/1117", "2026/1118"}
    assert by_id["2026/1117"].title == "On the Secrecy of the Encapsulation Coin in ML-KEM"


def test_iacr_latest_feed_mlkem_sample_enters_ranking_path() -> None:
    records = parse_iacr_feed(_latest_iacr_xml())
    configs = load_config_bundle(None)

    ranked = rank_records(records, configs["taxonomy"], configs["keywords"], configs["negative"])
    by_id = {record.eprint_id: record for record in ranked}

    assert by_id["2026/1117"].title == "On the Secrecy of the Encapsulation Coin in ML-KEM"
    assert by_id["2026/1117"].relevance_label == "A"
    assert by_id["2026/1117"].relevance_score == 100


def test_iacr_include_latest_sources_recovers_failed_attempt_and_reports_latest_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / f"iacr_eprint_{today}.attempt").write_text("failed earlier", encoding="utf-8")

    def latest_fetch_text(context, url, source_name):  # noqa: ANN001
        return _latest_iacr_xml()

    monkeypatch.setattr(iacr_module, "fetch_text", latest_fetch_text)
    context = _context(tmp_path, include_latest_sources=True)
    records = _source(expected_latest_ids=["2026/1115", "2026/1116", "2026/1117", "2026/1118"]).fetch(context)
    health = context.source_health_summary()[0]

    assert {record.eprint_id for record in records} == {"2026/1115", "2026/1116", "2026/1117", "2026/1118"}
    assert health["latest_feed_status"] == "manual_latest_retry"
    assert health["latest_feed_parsed"] is True
    assert health["latest_feed_records"] == 4
    assert health["latest_feed_missing_expected"] == []
    assert health["latest_feed_skipped_by_guard"] is False


def test_iacr_latest_feed_enters_run_and_ranking_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        """
request:
  timeout_seconds: 1
sources:
  - name: iacr_eprint
    type: iacr_eprint
    enabled: true
    url: "https://eprint.iacr.org/rss/rss.xml"
    expected_latest_ids:
      - 2026/1115
      - 2026/1116
      - 2026/1117
      - 2026/1118
""".strip(),
        encoding="utf-8",
    )
    for name in ("taxonomy.yaml", "keywords.yaml", "negative_keywords.yaml"):
        (config_dir / name).write_text(Path("config", name).read_text(encoding="utf-8"), encoding="utf-8")

    today = datetime.now(timezone.utc).date().isoformat()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / f"iacr_eprint_{today}.attempt").write_text("failed earlier", encoding="utf-8")

    def latest_fetch_text(context, url, source_name):  # noqa: ANN001
        return _latest_iacr_xml()

    monkeypatch.setattr(iacr_module, "fetch_text", latest_fetch_text)
    monkeypatch.setattr(run_module, "project_root", lambda: tmp_path)

    result = run_module.main(
        [
            "--target-date",
            "2026-06-01",
            "--since",
            "7d",
            "--output",
            "json",
            "--send",
            "none",
            "--config-dir",
            str(config_dir),
            "--include-latest-sources",
        ]
    )

    assert result == 0
    payload = json.loads(daily_data_path("2026-06-01", tmp_path / "data").read_text(encoding="utf-8"))
    by_id = {record.get("eprint_id"): record for record in payload["records"]}

    assert by_id["2026/1117"]["title"] == "On the Secrecy of the Encapsulation Coin in ML-KEM"
    assert by_id["2026/1117"]["relevance_label"] == "A"
    assert by_id["2026/1117"]["relevance_score"] == 100
    assert "2026/1115" not in by_id
    assert payload["source_health"][0]["latest_feed_status"] == "manual_latest_retry"
    assert payload["source_health"][0]["latest_feed_records"] == 4
    assert payload["source_health"][0]["latest_feed_missing_expected"] == []


def test_iacr_manual_retry_does_not_introduce_scheduler_code() -> None:
    combined = "\n".join(
        [
            Path("src/lattice_digest/sources/iacr.py").read_text(encoding="utf-8"),
            Path("src/lattice_digest/run.py").read_text(encoding="utf-8"),
        ]
    ).lower()

    assert "schtasks" not in combined
    assert "task scheduler" not in combined
    assert "cron" not in combined
    assert "startup task" not in combined
    assert "background service" not in combined
