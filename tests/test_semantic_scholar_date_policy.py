from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import lattice_digest.sources.semantic_scholar as semantic_scholar
from lattice_digest.sources.base import FetchContext
from lattice_digest.sources.semantic_scholar import SemanticScholarSource


def test_semantic_scholar_year_only_record_is_not_in_36h_digest() -> None:
    def fake_fetch_json(*args: object, **kwargs: object) -> dict:
        return {
            "data": [
                {
                    "paperId": "s2-year-only",
                    "title": "LWE Cryptanalysis with BKZ",
                    "abstract": "A lattice cryptanalysis paper with no reliable recent date.",
                    "authors": [{"name": "Alice Example"}],
                    "venue": "unknown",
                    "year": 2026,
                    "externalIds": {},
                    "url": "https://www.semanticscholar.org/paper/s2-year-only",
                }
            ]
        }

    original_fetch_json = semantic_scholar.fetch_json
    semantic_scholar.fetch_json = fake_fetch_json
    try:
        with TemporaryDirectory() as tmp:
            context = FetchContext(
                root=Path(tmp),
                since=datetime(2026, 1, 1, tzinfo=timezone.utc),
                dry_run=False,
            )
            source = SemanticScholarSource(
                {
                    "name": "semantic_scholar",
                    "type": "semantic_scholar",
                    "url": "https://api.semanticscholar.org/graph/v1/paper/search",
                    "exclude_year_only_from_since_window": True,
                }
            )

            records = source.fetch(context)
    finally:
        semantic_scholar.fetch_json = original_fetch_json

    assert records == []
    assert any("year-only" in warning for warning in context.warnings)
