from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
import hashlib
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit

from lattice_digest.models import PaperRecord, copy_record
from lattice_digest.text import normalize_title


PROVENANCE_ORDER = {
    "iacr_eprint": 6,
    "arxiv": 6,
    "crossref": 5,
    "dblp": 5,
    "semantic_scholar": 3,
    "openalex": 3,
}


@dataclass(frozen=True)
class MergeProposal:
    left_identity: str
    right_identity: str
    title_similarity: float
    rationale: str = "fuzzy title similarity without sufficient corroboration"
    decision: str = "MERGE_PROPOSAL"

    def to_dict(self) -> dict[str, object]:
        return {
            "left_identity": self.left_identity,
            "right_identity": self.right_identity,
            "title_similarity": self.title_similarity,
            "rationale": self.rationale,
            "decision": self.decision,
        }


@dataclass(frozen=True)
class IdentityResolution:
    canonical_records: tuple[PaperRecord, ...]
    merge_proposals: tuple[MergeProposal, ...]
    strong_merge_count: int
    secondary_merge_count: int
    conflict_count: int


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> bool:
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return False
        self.parent[right_root] = left_root
        return True


def resolve_identity_and_merge(records: Iterable[PaperRecord]) -> IdentityResolution:
    items = [copy_record(record) for record in records]
    union = _UnionFind(len(items))
    strong_indexes: dict[str, int] = {}
    strong_merge_count = 0
    secondary_merge_count = 0

    for index, record in enumerate(items):
        for key in strong_identity_keys(record):
            previous = strong_indexes.get(key)
            if previous is None:
                strong_indexes[key] = index
            elif union.union(index, previous):
                strong_merge_count += 1

    exact_title_groups: dict[str, list[int]] = {}
    for index, record in enumerate(items):
        title = record.normalized_title or normalize_title(record.title)
        if title:
            exact_title_groups.setdefault(title, []).append(index)
    for group in exact_title_groups.values():
        for position, left in enumerate(group):
            for right in group[position + 1 :]:
                if _secondary_identity_compatible(items[left], items[right]) and union.union(left, right):
                    secondary_merge_count += 1

    clusters: dict[int, list[PaperRecord]] = {}
    for index, record in enumerate(items):
        clusters.setdefault(union.find(index), []).append(record)

    canonical: list[PaperRecord] = []
    conflict_count = 0
    for cluster in clusters.values():
        merged, conflicts = merge_evidence_cluster(cluster)
        conflict_count += conflicts
        canonical.append(merged)

    proposals = _fuzzy_proposals(canonical)
    proposals_by_identity: dict[str, list[dict[str, object]]] = {}
    for proposal in proposals:
        proposals_by_identity.setdefault(proposal.left_identity, []).append(proposal.to_dict())
        proposals_by_identity.setdefault(proposal.right_identity, []).append(proposal.to_dict())
    for record in canonical:
        identity = canonical_identity(record)
        if identity in proposals_by_identity:
            record.merge_proposals = list(proposals_by_identity[identity])

    return IdentityResolution(
        canonical_records=tuple(canonical),
        merge_proposals=tuple(proposals),
        strong_merge_count=strong_merge_count,
        secondary_merge_count=secondary_merge_count,
        conflict_count=conflict_count,
    )


def strong_identity_keys(record: PaperRecord) -> tuple[str, ...]:
    keys: list[str] = []
    if record.doi:
        keys.append("doi:" + _normalize_doi(record.doi))
    if record.arxiv_id:
        keys.append("arxiv:" + _normalize_versioned_id(record.arxiv_id))
    if record.eprint_id:
        keys.append("eprint:" + _normalize_versioned_id(record.eprint_id))
    canonical_url = _canonical_url(record.source_url)
    if canonical_url and _official_identity_url(canonical_url):
        keys.append("url:" + canonical_url)
    return tuple(dict.fromkeys(keys))


def canonical_identity(record: PaperRecord) -> str:
    keys = strong_identity_keys(record)
    if keys:
        return keys[0]
    title = record.normalized_title or normalize_title(record.title)
    authors = ",".join(sorted(_normalized_authors(record)))
    year = _record_year(record) or "unknown"
    return f"title-author-year:{title}|{authors}|{year}"


def merge_evidence_cluster(records: list[PaperRecord]) -> tuple[PaperRecord, int]:
    strongest = max(records, key=_record_strength)
    merged = copy_record(strongest)
    conflicts: list[dict[str, object]] = []
    merged.source_urls = list(dict.fromkeys(url for record in records for url in [record.source_url, *record.source_urls] if url))
    merged.source_ids = _unique_dicts(
        {
            "source": record.source,
            "paper_id": record.paper_id or "",
            "doi": record.doi or "",
            "arxiv_id": record.arxiv_id or "",
            "eprint_id": record.eprint_id or "",
        }
        for record in records
    )
    merged.query_ids = list(
        dict.fromkeys(
            item
            for record in records
            for item in [record.source_query_family, *record.query_ids]
            if item
        )
    )
    merged.raw_occurrence_ids = list(
        dict.fromkeys(item for record in records for item in record.raw_occurrence_ids if item)
    )
    merged.date_evidence = _date_evidence(records)
    merged.evidence_versions = _evidence_versions(records)
    merged.content_hashes = list(
        dict.fromkeys(
            item
            for record in records
            for item in [*record.content_hashes, _content_hash(record)]
            if item
        )
    )
    merged.version_relations = _version_relations(records)
    merged.merge_rationale = [
        f"identity/evidence cluster merged {len(records)} occurrence(s)",
        *sorted({reason for record in records for reason in record.merge_rationale}),
    ]
    merged.provenance_strength = _provenance_label(_record_strength(strongest))
    merged.source = ", ".join(dict.fromkeys(record.source for record in records if record.source))
    merged.authors = list(dict.fromkeys(author for record in records for author in record.authors if author))
    merged.categories = sorted({item for record in records for item in record.categories})
    merged.source_evidence_terms = sorted({item for record in records for item in record.source_evidence_terms})
    merged.inferred_topic_tags = sorted({item for record in records for item in record.inferred_topic_tags})
    merged.taxonomy_tags = sorted({item for record in records for item in record.taxonomy_tags})
    merged.keywords_matched = sorted({item for record in records for item in record.keywords_matched})
    merged.negative_keywords_matched = sorted({item for record in records for item in record.negative_keywords_matched})
    merged.abstract = max((record.abstract or "" for record in records), key=len, default="")
    merged.conclusion = max((record.conclusion or "" for record in records), key=len, default="")

    for field in (
        "doi", "arxiv_id", "eprint_id", "paper_id", "publication_date", "publication_timestamp",
        "update_date", "update_timestamp", "venue", "pdf_url",
    ):
        values = list(dict.fromkeys(str(getattr(record, field)) for record in records if getattr(record, field)))
        if len(values) > 1 and field not in {"paper_id", "publication_timestamp", "update_timestamp"}:
            conflicts.append({"field": field, "values": values, "resolution": "strongest provenance retained"})
        if not getattr(merged, field) and values:
            setattr(merged, field, values[0])
    merged.conflicting_metadata = [*merged.conflicting_metadata, *conflicts]
    return merged, len(conflicts)


def _secondary_identity_compatible(left: PaperRecord, right: PaperRecord) -> bool:
    left_authors, right_authors = _normalized_authors(left), _normalized_authors(right)
    author_overlap = bool(left_authors.intersection(right_authors))
    left_year, right_year = _record_year(left), _record_year(right)
    compatible_year = not left_year or not right_year or abs(int(left_year) - int(right_year)) <= 1
    return author_overlap and compatible_year


def _fuzzy_proposals(records: list[PaperRecord], threshold: float = 0.92) -> list[MergeProposal]:
    proposals: list[MergeProposal] = []
    for index, left in enumerate(records):
        left_title = left.normalized_title or normalize_title(left.title)
        for right in records[index + 1 :]:
            right_title = right.normalized_title or normalize_title(right.title)
            if not left_title or not right_title or left_title == right_title:
                continue
            similarity = SequenceMatcher(None, left_title, right_title).ratio()
            if similarity >= threshold:
                proposals.append(
                    MergeProposal(
                        left_identity=canonical_identity(left),
                        right_identity=canonical_identity(right),
                        title_similarity=round(similarity, 6),
                    )
                )
    return proposals


def _record_strength(record: PaperRecord) -> tuple[int, int, int, int]:
    sources = [item.strip() for item in record.source.split(",")]
    provenance = max((PROVENANCE_ORDER.get(item, 1) for item in sources), default=1)
    identifier_count = sum(bool(value) for value in (record.doi, record.arxiv_id, record.eprint_id))
    authoritative_date = int(record.publication_date_kind == "AUTHORITATIVE_PUBLICATION_DATE" and bool(record.publication_date))
    return provenance, identifier_count, authoritative_date, len(record.abstract or "")


def _provenance_label(strength: tuple[int, int, int, int]) -> str:
    if strength[0] >= 6:
        return "primary_source"
    if strength[0] >= 5:
        return "authoritative_metadata"
    if strength[0] >= 3:
        return "aggregated_metadata"
    return "unknown"


def _date_evidence(records: Iterable[PaperRecord]) -> list[dict[str, str | None]]:
    evidence: list[dict[str, str | None]] = []
    for record in records:
        for field, kind_field in (
            ("publication_date", "publication_date_kind"),
            ("update_date", "update_date_kind"),
            ("announcement_date", "announcement_date_kind"),
            ("first_seen_at", None),
            ("source_observed_at", None),
        ):
            value = getattr(record, field)
            if value:
                evidence.append(
                    {
                        "source": record.source,
                        "source_url": record.source_url,
                        "field": field,
                        "value": value,
                        "semantics": getattr(record, kind_field) if kind_field else field.upper(),
                    }
                )
    return _unique_dicts(evidence)


def _evidence_versions(records: Iterable[PaperRecord]) -> list[dict[str, object]]:
    versions: list[dict[str, object]] = []
    for record in records:
        versions.append(
            {
                "source": record.source,
                "source_url": record.source_url,
                "abstract_present": bool(record.abstract),
                "abstract_hash": hashlib.sha256((record.abstract or "").encode("utf-8")).hexdigest() if record.abstract else "",
                "retrieved_at": record.retrieval_timestamp or record.source_observed_at or "unknown",
            }
        )
    return _unique_dicts(versions)


def _version_relations(records: list[PaperRecord]) -> list[dict[str, str]]:
    relations: list[dict[str, str]] = []
    identifiers = [(record.source, canonical_identity(record)) for record in records]
    for index, (left_source, left_id) in enumerate(identifiers):
        for right_source, right_id in identifiers[index + 1 :]:
            if left_id != right_id or left_source != right_source:
                relations.append(
                    {
                        "relation_type": "VERSION_OF",
                        "left": left_id,
                        "right": right_id,
                        "rationale": "corroborated identity cluster; publication and preprint metadata preserved separately",
                    }
                )
    return _unique_dicts(relations)


def _content_hash(record: PaperRecord) -> str:
    payload = "|".join([record.title, record.abstract or "", record.conclusion or "", record.source_url])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalized_authors(record: PaperRecord) -> set[str]:
    return {" ".join(author.lower().replace(",", " ").split()) for author in record.authors if author.strip()}


def _record_year(record: PaperRecord) -> str | None:
    for value in (record.publication_date, record.update_date):
        if value and len(value) >= 4 and value[:4].isdigit():
            return value[:4]
    return None


def _normalize_doi(value: str) -> str:
    normalized = value.lower().strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized.rstrip("/.")


def _normalize_versioned_id(value: str) -> str:
    normalized = value.lower().strip()
    if "v" in normalized and normalized.rsplit("v", 1)[-1].isdigit():
        normalized = normalized.rsplit("v", 1)[0]
    return normalized


def _canonical_url(value: str) -> str:
    try:
        parsed = urlsplit(str(value or "").strip())
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    path = parsed.path.rstrip("/")
    return urlunsplit(("https", parsed.netloc.lower(), path, "", ""))


def _official_identity_url(value: str) -> bool:
    host = urlsplit(value).netloc.lower()
    return host in {
        "arxiv.org", "export.arxiv.org", "eprint.iacr.org", "doi.org", "dblp.org", "www.dblp.org",
        "openalex.org", "api.openalex.org", "semanticscholar.org", "www.semanticscholar.org",
    }


def _unique_dicts(values: Iterable[dict]) -> list[dict]:
    result: list[dict] = []
    seen: set[str] = set()
    for value in values:
        marker = repr(sorted(value.items()))
        if marker not in seen:
            seen.add(marker)
            result.append(value)
    return result
