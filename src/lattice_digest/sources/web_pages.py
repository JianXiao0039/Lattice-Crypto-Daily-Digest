from __future__ import annotations

from lattice_digest.models import PaperRecord
from lattice_digest.sources.base import FetchContext, SourceAdapter


class HtmlProgramPagesSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        context.warnings.append(
            f"{self.name}: HTML accepted-papers scraping is disabled by default; prefer API/RSS/Atom/OAI-PMH sources"
        )
        return []

