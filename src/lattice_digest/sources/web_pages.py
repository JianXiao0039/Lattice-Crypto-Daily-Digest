from __future__ import annotations

from lattice_digest.models import PaperRecord
from lattice_digest.sources.base import FetchContext, SourceAdapter


class HtmlProgramPagesSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        context.add_warning(
            f"{self.name}: HTML accepted-papers scraping is disabled by default; prefer API/RSS/Atom/OAI-PMH sources",
            self.name,
        )
        context.set_source_counts(self.name, raw=0, normalized=0, date_filtered=0)
        return []
