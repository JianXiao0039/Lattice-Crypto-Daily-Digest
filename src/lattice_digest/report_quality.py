from __future__ import annotations

from typing import Any


ANCHOR_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("LWE/RLWE/MLWE", ("lwe", "learning with errors", "rlwe", "ring-lwe", "mlwe", "module-lwe", "module lwe")),
    ("SIS/Module-SIS", ("module-sis", "module sis", "short integer solution", " sis", "sis ")),
    ("NTRU", ("ntru",)),
    ("ML-KEM/Kyber", ("ml-kem", "kyber")),
    ("ML-DSA/Dilithium", ("ml-dsa", "dilithium")),
    ("Falcon/FN-DSA", ("fn-dsa", "falcon signature", "falcon/fn-dsa")),
    ("FHE/HE", ("fully homomorphic encryption", "homomorphic encryption", "fhe", "ckks", "bfv", "bgv", "tfhe")),
    ("lattice-based primitive", ("lattice-based", "lattice commitment", "sis commitment", "module-sis commitment", "chameleon hash")),
    ("PQC anchor", ("post-quantum", "pqc", "nist pqc", "quantum-safe", "quantum resistant")),
    ("lattice", ("lattice cryptography", "lattice-based", "lattice scheme", "lattice schemes")),
    ("BKZ/lattice attack", ("bkz", "lll", "g6k", "fplll", "lattice reduction", "primal attack", "dual attack", "hybrid attack")),
    ("AI-assisted lattice", ("ai-assisted lattice", "neural lattice", "transformer lwe", "machine learning lwe")),
)

GENERIC_RISK_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("generic privacy/FL/LLM", ("privacy-preserving", "federated learning", "secure aggregation", "llm", "gradient boosting", "gbdt")),
    ("generic ZK/credential", ("zero-knowledge", "anonymous credential", "credential")),
    ("generic registration/isomorphism", ("registration", "isomorphism")),
    ("generic Falcon-name collision", ("falcon-x", "foundation model")),
)


def _field(record: Any, *names: str) -> Any:
    for name in names:
        if isinstance(record, dict) and name in record:
            return record.get(name)
        if hasattr(record, name):
            return getattr(record, name)
    return None


def _list_field(record: Any, *names: str) -> list[str]:
    value = _field(record, *names)
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if value:
        return [str(value)]
    return []


def record_text(record: Any) -> str:
    parts: list[str] = []
    for key in (
        "title",
        "abstract",
        "summary",
        "reason",
        "reason_for_priority",
        "why_it_matters",
        "source",
        "venue",
    ):
        value = _field(record, key)
        if value:
            parts.append(str(value))
    parts.extend(_list_field(record, "taxonomy_tags"))
    parts.extend(_list_field(record, "keywords_matched"))
    parts.extend(_list_field(record, "research_tags", "tags"))
    parts.extend(_list_field(record, "research_sections"))
    ranking = _field(record, "ranking_explanation")
    if isinstance(ranking, dict):
        for key in ("matched_taxonomy", "positive_signals", "negative_signals", "notes"):
            parts.extend(_list_field(ranking, key))
    metadata = _semantic_metadata(record)
    if metadata:
        parts.append(str(metadata.get("title") or ""))
        parts.append(str(metadata.get("abstract") or ""))
        parts.append(str(metadata.get("venue") or ""))
        external = metadata.get("externalIds")
        if isinstance(external, dict):
            parts.extend(str(value) for value in external.values() if value)
    return " ".join(parts).lower()


def lattice_pqc_anchor_evidence(record: Any) -> list[str]:
    text = f" {record_text(record)} "
    anchors: list[str] = []
    for label, patterns in ANCHOR_PATTERNS:
        if any(pattern in text for pattern in patterns):
            anchors.append(label)
    return anchors


def anchor_evidence_text(record: Any) -> str:
    anchors = lattice_pqc_anchor_evidence(record)
    if not anchors:
        return "lattice/PQC anchor evidence: not detected; manual review required"
    return "lattice/PQC anchor evidence: " + "；".join(anchors)


def false_positive_risk_notes(record: Any) -> list[str]:
    text = f" {record_text(record)} "
    anchors = lattice_pqc_anchor_evidence(record)
    notes: list[str] = []
    for label, patterns in GENERIC_RISK_PATTERNS:
        if any(pattern in text for pattern in patterns) and not anchors:
            notes.append(f"{label}: 未见明确 lattice/PQC anchor，避免过度声称。")
    return notes


def false_positive_risk_text(record: Any) -> str:
    notes = false_positive_risk_notes(record)
    return "；".join(notes) if notes else "未发现明显 false-positive 风险信号。"


def _semantic_metadata(record: Any) -> dict[str, Any]:
    direct = _field(record, "semantic_scholar_metadata")
    if isinstance(direct, dict):
        return direct
    enrichment = _field(record, "semantic_scholar_enrichment")
    if isinstance(enrichment, dict):
        metadata = enrichment.get("metadata")
        if isinstance(metadata, dict):
            return metadata
    return {}


def semantic_scholar_advisory_text(record: Any) -> str:
    metadata = _semantic_metadata(record)
    if not metadata:
        return "无 Semantic Scholar enrichment metadata；不影响 ranking。"
    external = metadata.get("externalIds") if isinstance(metadata.get("externalIds"), dict) else {}
    doi = external.get("DOI") or _field(record, "doi")
    pdf = metadata.get("openAccessPdf") if isinstance(metadata.get("openAccessPdf"), dict) else {}
    values = [
        f"year={metadata.get('year') or 'unknown'}",
        f"venue={metadata.get('venue') or 'unknown'}",
        f"citationCount={metadata.get('citationCount') if metadata.get('citationCount') is not None else 'unknown'}",
        "influentialCitationCount="
        f"{metadata.get('influentialCitationCount') if metadata.get('influentialCitationCount') is not None else 'unknown'}",
        f"DOI={doi or 'unknown'}",
        f"CorpusId={metadata.get('corpusId') or 'unknown'}",
        f"openAccessPdf={pdf.get('url') or 'unknown'}",
    ]
    return "；".join(values) + "。仅作 advisory context，不覆盖 A/B/C ranking。"


def source_health_caveat_text(source_health: list[dict[str, object]] | dict[str, Any] | None) -> str:
    if not source_health:
        return "未提供 source health；覆盖率需要人工保守判断。"
    rows: list[dict[str, Any]]
    if isinstance(source_health, dict):
        raw_rows = source_health.get("records") if isinstance(source_health.get("records"), list) else []
        rows = [row for row in raw_rows if isinstance(row, dict)]
        if not rows and source_health.get("available") is False:
            return str(source_health.get("note") or "无 source health 数据；覆盖率需要人工保守判断。")
    else:
        rows = [row for row in source_health if isinstance(row, dict)]
    if not rows:
        return "无 source health 明细；覆盖率需要人工保守判断。"
    weak = [
        str(row.get("source") or "unknown")
        for row in rows
        if str(row.get("health_status") or row.get("status") or "").lower() in {"red", "yellow", "failed", "degraded"}
    ]
    if not weak:
        return "source health 未显示明显红/黄降级；仍需注意外部源更新延迟。"
    return "存在降级 source，报告覆盖率需保守解释：" + "，".join(sorted(set(weak)))
