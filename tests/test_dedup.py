from __future__ import annotations

from lattice_digest.dedup import deduplicate
from lattice_digest.models import make_paper_record


def test_deduplicate_merges_by_arxiv_id() -> None:
    first = make_paper_record(
        title="LWE Cryptanalysis with BKZ",
        authors=["Alice"],
        abstract="short",
        source="arxiv",
        source_url="https://arxiv.org/abs/2601.00001",
        arxiv_id="2601.00001",
    )
    second = make_paper_record(
        title="LWE Cryptanalysis with BKZ",
        authors=["Bob"],
        abstract="a longer abstract about LWE and BKZ",
        source="semantic_scholar",
        source_url="https://www.semanticscholar.org/paper/example",
        arxiv_id="2601.00001",
    )

    records = deduplicate([first, second])

    assert len(records) == 1
    assert records[0].authors == ["Alice", "Bob"]
    assert records[0].abstract == "a longer abstract about LWE and BKZ"
    assert records[0].source == "arxiv, semantic_scholar"


def test_deduplicate_merges_by_normalized_title() -> None:
    first = make_paper_record(
        title="A Note on Module-LWE Signatures",
        source="openalex",
        source_url="https://openalex.org/W1",
    )
    second = make_paper_record(
        title="A Note on Module LWE Signatures!",
        source="crossref",
        source_url="https://doi.org/10.0000/example",
    )

    records = deduplicate([first, second])

    assert len(records) == 1

