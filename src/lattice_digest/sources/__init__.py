from __future__ import annotations

from lattice_digest.sources.arxiv import ArxivSource
from lattice_digest.sources.base import FetchContext, SourceAdapter
from lattice_digest.sources.crossref import CrossrefSource
from lattice_digest.sources.dblp import DblpSource
from lattice_digest.sources.iacr import IacrEprintSource
from lattice_digest.sources.openalex import OpenAlexSource
from lattice_digest.sources.semantic_scholar import SemanticScholarSource
from lattice_digest.sources.web_pages import HtmlProgramPagesSource

ADAPTERS = {
    "iacr_eprint": IacrEprintSource,
    "arxiv": ArxivSource,
    "dblp": DblpSource,
    "openalex": OpenAlexSource,
    "crossref": CrossrefSource,
    "semantic_scholar": SemanticScholarSource,
    "html_program_pages": HtmlProgramPagesSource,
}


def build_source(config: dict) -> SourceAdapter:
    source_type = config.get("type")
    adapter_cls = ADAPTERS.get(source_type)
    if not adapter_cls:
        raise ValueError(f"Unsupported source type: {source_type}")
    return adapter_cls(config)

