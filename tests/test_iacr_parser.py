from __future__ import annotations

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

