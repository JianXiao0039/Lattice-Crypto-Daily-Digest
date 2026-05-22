from __future__ import annotations

from lattice_digest.sources.arxiv import parse_arxiv_atom


def test_arxiv_atom_parser_extracts_record() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>http://arxiv.org/abs/2601.00001v2</id>
        <updated>2026-05-22T00:00:00Z</updated>
        <published>2026-05-21T00:00:00Z</published>
        <title>BKZ Attacks on LWE</title>
        <summary>We analyze post-quantum cryptanalysis of LWE using BKZ.</summary>
        <author><name>Alice Example</name></author>
        <author><name>Bob Example</name></author>
        <category term="cs.CR" scheme="http://arxiv.org/schemas/atom"/>
        <link title="pdf" href="http://arxiv.org/pdf/2601.00001v2" rel="related" type="application/pdf"/>
        <arxiv:doi>10.0000/example</arxiv:doi>
      </entry>
    </feed>
    """

    records = parse_arxiv_atom(xml)

    assert len(records) == 1
    record = records[0]
    assert record.title == "BKZ Attacks on LWE"
    assert record.authors == ["Alice Example", "Bob Example"]
    assert record.arxiv_id == "2601.00001"
    assert record.doi == "10.0000/example"
    assert record.categories == ["cs.CR"]
    assert record.pdf_url == "http://arxiv.org/pdf/2601.00001v2"

