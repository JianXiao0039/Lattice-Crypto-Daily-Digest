"""Small source-coverage receipts, separate from transport and paper validity.

Exhausting an API query proves coverage of that expression only. A bounded
latest feed never proves coverage of an historical publication interval.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

OPEN_SEARCH = "http://a9.com/-/spec/opensearch/1.1/"


def arxiv_page_bounds(root: ET.Element, *, requested_start: int, entries: int) -> tuple[int | None, str | None]:
    """Validate official OpenSearch counters without treating absent totals as 0."""
    total_text = root.findtext(f"{{{OPEN_SEARCH}}}totalResults")
    start_text = root.findtext(f"{{{OPEN_SEARCH}}}startIndex")
    if total_text is None or start_text is None:
        return None, "ARXIV_PAGINATION_METADATA_MISSING"
    try:
        total, start = int(total_text), int(start_text)
    except (TypeError, ValueError):
        return None, "ARXIV_PAGINATION_METADATA_INVALID"
    if total < 0 or start != requested_start or total < start + entries:
        return None, "ARXIV_PAGINATION_METADATA_INCONSISTENT"
    if entries == 0 and total > requested_start:
        return total, "ARXIV_EMPTY_PAGE_BEFORE_EXHAUSTION"
    return total, None


def record_source_coverage(context, source: str, *, state: str, reason: str, **details: object) -> None:
    """Keep bounded derived coverage diagnostics without erasing raw failures."""
    health = context.health(source)
    receipt = {"kind": "source_coverage_v1", "coverage_state": state, "reason_code": reason, **details}
    # Reserve only a compact receipt; raw request diagnostics remain untouched.
    if len(health.request_diagnostics) < 64:
        health.request_diagnostics.append(receipt)
    context.checkpoint("SOURCE_COVERAGE", {"source": source, **receipt})
    if state != "SOURCE_COMPLETE":
        health.runtime_state = "partial" if state == "SOURCE_PARTIAL" else "failed"
        if not health.runtime_reason_code:
            health.runtime_reason_code = reason


def bounded_page_budget(config: dict, key: str, *, default: int, maximum: int) -> int:
    value = int(config.get(key, default))
    return max(0, min(value, maximum))
