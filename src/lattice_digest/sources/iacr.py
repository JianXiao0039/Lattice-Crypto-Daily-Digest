from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

from lattice_digest.models import PaperRecord, make_paper_record
from lattice_digest.sources.base import FetchContext, SourceAdapter, fetch_text, normalize_date
from lattice_digest.text import normalize_whitespace
from lattice_digest.source_queries import native_feed_query_request
from lattice_digest.source_completeness import record_source_coverage

EPRINT_RE = re.compile(r"eprint\.iacr\.org/(?:eprint-bin/)?(?:archive/)?(\d{4}/\d+)", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in element:
        if _local_name(child.tag) in wanted and child.text:
            return normalize_whitespace(html.unescape(child.text))
    return ""


def _all_child_text(element: ET.Element, name: str) -> list[str]:
    found = []
    for child in element:
        if _local_name(child.tag) == name.lower() and child.text:
            found.append(normalize_whitespace(html.unescape(child.text)))
    return found


def _clean_abstract(value: str) -> str:
    return normalize_whitespace(TAG_RE.sub(" ", html.unescape(value or "")))


def _extract_eprint_id(*values: str) -> str | None:
    for value in values:
        match = EPRINT_RE.search(value or "")
        if match:
            return match.group(1)
    joined = " ".join(values)
    match = re.search(r"\b(\d{4}/\d{3,5})\b", joined)
    return match.group(1) if match else None


def parse_iacr_feed(xml_text: str, source_url: str = "https://eprint.iacr.org/rss/rss.xml") -> list[PaperRecord]:
    root = ET.fromstring(xml_text)
    if _local_name(root.tag) not in {"rss", "feed", "rdf"}:
        raise ET.ParseError("expected IACR RSS/Atom feed, received another document")
    records: list[PaperRecord] = []

    rss_items = [element for element in root.iter() if _local_name(element.tag) == "item"]
    atom_entries = [element for element in root.iter() if _local_name(element.tag) == "entry"]
    items = rss_items or atom_entries

    for item in items:
        title = _child_text(item, "title")
        link = _child_text(item, "link", "id")
        if not link:
            for child in item:
                if _local_name(child.tag) == "link" and child.attrib.get("href"):
                    link = child.attrib["href"]
                    break
        abstract = _clean_abstract(_child_text(item, "description", "summary", "abstract"))
        authors = _all_child_text(item, "creator")
        for child in item:
            if _local_name(child.tag) == "author":
                author_name = _child_text(child, "name") or normalize_whitespace(child.text)
                if author_name:
                    authors.append(author_name)
        publication_text = _child_text(item, "pubdate", "published", "date")
        update_text = _child_text(item, "updated")
        publication_date = normalize_date(publication_text)
        update_date = normalize_date(update_text)
        eprint_id = _extract_eprint_id(link, title)
        pdf_url = f"https://eprint.iacr.org/{eprint_id}.pdf" if eprint_id else None
        if not title or not link:
            continue
        records.append(
            make_paper_record(
                title=title,
                authors=list(dict.fromkeys(authors)),
                abstract=abstract,
                source="iacr_eprint",
                source_url=link,
                pdf_url=pdf_url,
                paper_id=f"iacr:{eprint_id}" if eprint_id else link,
                eprint_id=eprint_id,
                venue="IACR ePrint",
                publication_date=publication_date,
                publication_timestamp=publication_text or None,
                update_date=update_date,
                update_timestamp=update_text or None,
                categories=["iacr_eprint"],
            )
        )
    return records


class IacrEprintSource(SourceAdapter):
    def fetch(self, context: FetchContext) -> list[PaperRecord]:
        latest = self._fetch_latest(context)
        if context.dry_run or not self.config.get("historical_catchup_enabled", False):
            return latest
        from lattice_digest.source_batch_iacr import fetch_iacr_days
        historical = fetch_iacr_days(context, self.config, fetch_text)
        # Stable ID dedup; both raw source occurrences remain in the trace.
        by_id = {record.eprint_id or record.paper_id: record for record in latest}
        for record in historical:
            by_id.setdefault(record.eprint_id or record.paper_id, record)
        combined = list(by_id.values())
        context.set_source_counts(self.name,
            raw=context.health(self.name).raw_candidates + len(historical),
            normalized=len(combined), observability=len(combined), date_filtered=0)
        return combined

    def _fetch_latest(self, context: FetchContext) -> list[PaperRecord]:
        url = self.config["url"]
        request = native_feed_query_request(self.config, family_id="native_iacr_latest_feed", expression=url)
        attempt_id = context.begin_query_attempt(self.name, request)
        if context.dry_run:
            context.finish_query_attempt(attempt_id, status="dry_run", raw_candidates=None)
            context.set_latest_feed_state(self.name, status="dry_run", reachable=None, parsed=False, records=0)
            context.add_warning("dry-run: skipped IACR ePrint network request", self.name)
            return []

        assert context.cache_dir is not None
        context.cache_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.now(timezone.utc).date().isoformat()
        cache_path = context.cache_dir / f"iacr_eprint_{today}.xml"
        attempt_path = context.cache_dir / f"iacr_eprint_{today}.attempt"
        latest_feed_status = "fetched"
        now = datetime.now(timezone.utc)
        attempt_count = 0
        retry_at = None
        marker_unknown = False
        if attempt_path.exists():
            marker = attempt_path.read_text(encoding="utf-8")
            try:
                saved = json.loads(marker)
                attempt_count = max(1, int(saved["attempts"]))
                retry_at = datetime.fromisoformat(saved["next_eligible_retry"])
                if retry_at.tzinfo is None:
                    raise ValueError("naive marker")
            except (ValueError, TypeError, KeyError):
                # Legacy markers without reliable timing require explicit retry.
                attempt_count = 1
                marker_unknown = True
        if cache_path.exists():
            xml_text = cache_path.read_text(encoding="utf-8")
            latest_feed_status = "cache_hit"
            observed_at = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=timezone.utc).isoformat()
        else:
            manual = context.retry_failed_sources or context.include_latest_sources
            maximum = min(2, max(1, int(self.config.get("max_transport_attempts_per_day", 2))))
            retry_enabled = "retry_failed_after_seconds" in self.config
            eligible = attempt_count < maximum and (not attempt_count or manual or
                        (retry_enabled and not marker_unknown and retry_at is not None and now >= retry_at))
            if not eligible:
                context.finish_query_attempt(attempt_id, status="skipped_by_guard", raw_candidates=None)
                context.set_latest_feed_state(self.name, status="skipped_by_guard", reachable=None,
                                              parsed=False, records=0, skipped_by_guard=True)
                context.add_warning("IACR ePrint already requested today; failed-attempt guard defers retry; no successful snapshot", self.name)
                record_source_coverage(context, self.name, state="SOURCE_UNAVAILABLE",
                    reason="IACR_DAILY_GUARD_NO_SNAPSHOT", requested_since=context.since.isoformat(),
                    next_eligible_retry=retry_at.isoformat() if retry_at else None,
                    attempts=attempt_count, observed_items=None)
                return []
            latest_feed_status = ("manual_latest_retry" if context.include_latest_sources else "manual_retry") if attempt_count else "fetched"
            if attempt_count and manual:
                context.add_warning("manual retry enabled for IACR ePrint after previous failed same-day attempt", self.name)
            delay = max(21600, int(self.config.get("retry_failed_after_seconds", 21600)))
            receipt = {"schema_version": "iacr-attempt-v44", "attempts": attempt_count + 1,
                       "attempt_time": now.isoformat(), "requested_interval": [context.since.isoformat(), now.isoformat()],
                       "next_eligible_retry": (now + timedelta(seconds=delay)).isoformat(),
                       "response_status": "ATTEMPT_IN_PROGRESS", "error_reason": None,
                       "unverified_interval": [context.since.isoformat(), now.isoformat()]}
            attempt_path.write_text(json.dumps(receipt), encoding="utf-8")
            xml_text = fetch_text(context, url, source_name=self.name)
            if xml_text is None:
                receipt.update(response_status="TRANSPORT_FAILED", error_reason=context.health(self.name).error_type())
                attempt_path.write_text(json.dumps(receipt), encoding="utf-8")
                context.finish_query_attempt(attempt_id, status="failed", raw_candidates=None,
                                             error_category=context.health(self.name).error_type())
                context.set_latest_feed_state(self.name, status="failed", reachable=False, parsed=False, records=0)
                record_source_coverage(context, self.name, state="SOURCE_UNAVAILABLE", reason="IACR_FEED_FETCH_FAILED",
                    requested_since=context.since.isoformat(), next_eligible_retry=receipt["next_eligible_retry"], observed_items=None)
                return []
            observed_at = datetime.now(timezone.utc).isoformat()

        try:
            root = ET.fromstring(xml_text)
            normalized = parse_iacr_feed(xml_text, source_url=url)
            rss_items = [element for element in root.iter() if _local_name(element.tag) == "item"]
            atom_entries = [element for element in root.iter() if _local_name(element.tag) == "entry"]
            raw_count = len(rss_items or atom_entries)
        except (ET.ParseError, ValueError) as exc:
            if latest_feed_status != "cache_hit":
                receipt.update(response_status="PARSE_FAILED", error_reason=str(exc))
                attempt_path.write_text(json.dumps(receipt), encoding="utf-8")
            context.finish_query_attempt(attempt_id, status="failed", raw_candidates=None, error_category="parse_error")
            context.set_latest_feed_state(self.name, status="parse_failed", reachable=True, parsed=False)
            context.add_warning(f"IACR ePrint feed parse failed: {exc}", self.name)
            record_source_coverage(context, self.name, state="SOURCE_UNAVAILABLE", reason="IACR_FEED_PARSE_FAILED",
                                   requested_since=context.since.isoformat(), observed_items=None)
            return []
        if latest_feed_status != "cache_hit":
            # Never promote malformed HTML/XML into a successful daily cache.
            cache_path.write_text(xml_text, encoding="utf-8")
            receipt.update(response_status="SUCCESS_BOUNDED_LATEST", error_reason=None)
            attempt_path.write_text(json.dumps(receipt), encoding="utf-8")
        context.finish_query_attempt(attempt_id, status="success", raw_candidates=raw_count)
        traced: list[PaperRecord] = []
        for record in normalized:
            occurrence_id = context.record_raw_occurrence(
                self.name,
                attempt_id,
                raw_title=record.title,
                source_identifier=record.eprint_id or record.paper_id,
                source_url=record.source_url,
                publication_date=record.publication_date,
                update_date=record.update_date,
                abstract_present=bool(record.abstract),
                parser_result="PARSED",
            )
            record = record.model_copy(
                update={
                    "source_query_family": "native_iacr_latest_feed",
                    "source_query_text": url,
                    "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
                    "raw_occurrence_ids": [occurrence_id],
                    "query_ids": [request.query_id],
                }
            )
            context.record_normalized_candidate(occurrence_id, record)
            traced.append(record)
        normalized = traced
        expected_ids = [str(item) for item in self.config.get("expected_latest_ids", [])]
        found_ids = {record.eprint_id for record in normalized if record.eprint_id}
        missing_expected = [item for item in expected_ids if item not in found_ids]
        # The source-native latest feed is already bounded. Keep its normalized
        # candidates for central relevance/freshness routing so an older-dated,
        # newly observed CRITICAL item cannot disappear before classification.
        filtered = [
            record.model_copy(update={"first_seen_at": observed_at, "source_observed_at": observed_at})
            for record in normalized
        ]
        context.set_latest_feed_state(
            self.name,
            status=latest_feed_status,
            reachable=True,
            parsed=True,
            records=raw_count,
            missing_expected=missing_expected,
            skipped_by_guard=False,
        )
        context.set_source_counts(
            self.name,
            raw=raw_count,
            normalized=len(normalized),
            observability=len(filtered),
            date_filtered=0,
        )
        record_source_coverage(context, self.name, state="SOURCE_PARTIAL", reason="IACR_LATEST_FEED_NOT_HISTORICAL_COVERAGE",
                               scope="SOURCE_NATIVE_BOUNDED_LATEST_FEED", requested_since=context.since.isoformat(),
                               observed_items=raw_count, parsed_items=len(normalized), missing_expected_count=len(missing_expected),
                               earliest_publication_date=min((record.publication_date for record in normalized if record.publication_date), default=None),
                               original_snapshot_observed_at=observed_at,
                               historical_window_complete=False)
        return filtered
