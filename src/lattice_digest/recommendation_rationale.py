from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from lattice_digest.text import normalize_whitespace


CONFIDENCE_VALUES = {
    "conclusion_supported",
    "abstract_supported",
    "repository_note_supported",
    "metadata_supported",
    "title_only",
    "insufficient_evidence",
}

LATTICE_TERMS = (
    "lattice",
    "lwe",
    "rlwe",
    "mlwe",
    "module-lwe",
    "module lwe",
    "sis",
    "module-sis",
    "module sis",
    "ntru",
    "bkz",
    "lll",
    "svp",
    "cvp",
    "ml-kem",
    "kyber",
    "ml-dsa",
    "dilithium",
    "falcon",
    "fhe",
    "fully homomorphic",
    "homomorphic encryption",
    "ckks",
    "bfv",
    "bgv",
    "tfhe",
)

METHOD_CUES = (
    "propose",
    "proposes",
    "present",
    "presents",
    "introduce",
    "introduces",
    "construct",
    "constructs",
    "design",
    "designs",
    "develop",
    "develops",
    "attack",
    "attacks",
    "implement",
    "implements",
    "evaluate",
    "evaluates",
    "analyze",
    "analyses",
    "analyzes",
    "study",
    "studies",
    "benchmark",
    "benchmarks",
)

CONTRIBUTION_CUES = (
    "show",
    "shows",
    "demonstrate",
    "demonstrates",
    "achieve",
    "achieves",
    "improve",
    "improves",
    "first",
    "new",
    "novel",
    "result",
    "results",
    "contribution",
    "efficient",
    "practical",
    "competitive",
)

APPLICATION_CUES = (
    "gbdt",
    "gradient boosting",
    "analytics",
    "healthcare",
    "finance",
    "machine learning",
    "secure computation",
    "private set intersection",
    "psi",
)


@dataclass(frozen=True)
class RecommendationRationale:
    problem_summary: str
    method_summary: str
    contribution_summary: str
    evidence_basis: list[str]
    radar_relevance: str
    recommendation_reason: str
    caveat: str
    confidence: str
    source_fields_used: list[str] = field(default_factory=list)
    todo_verify: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_recommendation_rationale(record: Mapping[str, Any] | Any) -> RecommendationRationale:
    """Build a deterministic, evidence-scoped reading rationale for one paper.

    This helper is intentionally independent from ranking, taxonomy, source
    fetching, and digest rendering. It explains available metadata; it does not
    change inclusion, score, label, or production track assignment.
    """

    title = _field(record, "title", "paper_title")
    abstract = _field(record, "abstract", "summary", "abstract_text")
    conclusion = _field(record, "conclusion", "conclusion_text")
    notes = _field(record, "repository_notes", "notes", "reason_for_priority", "why_it_matters")
    source = _field(record, "source", "venue")
    keywords = _list_field(record, "keywords_matched", "keywords", "taxonomy_tags", "research_tags", "tags")

    source_fields = _source_fields(
        title=title,
        abstract=abstract,
        conclusion=conclusion,
        notes=notes,
        source=source,
        keywords=keywords,
    )
    evidence_basis = _evidence_basis(
        abstract=abstract,
        conclusion=conclusion,
        notes=notes,
        source=source,
        keywords=keywords,
        title=title,
    )
    confidence = _confidence(evidence_basis)
    relevant_terms = _matched_terms(" ".join([title, abstract, conclusion, notes, " ".join(keywords)]), LATTICE_TERMS)

    if abstract:
        sentences = _sentences(abstract)
        problem = _problem_summary(title, sentences)
        method = _cue_summary(sentences, METHOD_CUES, "摘要未明确给出方法、构造、攻击或系统细节；需要精读原文确认。")
        contribution = _cue_summary(
            _sentences(conclusion) if conclusion else sentences,
            CONTRIBUTION_CUES,
            "可用元数据未明确陈述贡献；需要核对全文中的贡献列表或实验结果。",
        )
    elif notes and not _only_keywords(keywords, notes):
        problem = f"仓库备注显示该论文与雷达关注点有关：{_clip(notes)}"
        method = "仓库备注不足以可靠抽取方法；TODO_VERIFY：需回到摘要或原文确认技术路线。"
        contribution = "仓库备注不足以可靠抽取贡献；TODO_VERIFY：需核对论文贡献声明。"
    elif title:
        problem = f"仅根据标题可确认主题为：{_clip(title)}"
        method = "仅有标题/关键词，不能可靠判断具体方法、构造、攻击或系统。"
        contribution = "仅有标题/关键词，不能可靠判断论文声称的新贡献。"
    else:
        problem = "记录缺少标题和摘要，无法可靠概括问题。"
        method = "证据不足，不能概括方法。"
        contribution = "证据不足，不能概括贡献。"

    radar_relevance = _radar_relevance(title, abstract, notes, keywords, relevant_terms)
    recommendation_reason = _recommendation_reason(
        title=title,
        confidence=confidence,
        radar_relevance=radar_relevance,
        relevant_terms=relevant_terms,
    )
    todo_verify = _todo_verify(abstract=abstract, conclusion=conclusion, relevant_terms=relevant_terms)
    caveat = _caveat(confidence, abstract=abstract, conclusion=conclusion, relevant_terms=relevant_terms)

    return RecommendationRationale(
        problem_summary=problem,
        method_summary=method,
        contribution_summary=contribution,
        evidence_basis=evidence_basis,
        radar_relevance=radar_relevance,
        recommendation_reason=recommendation_reason,
        caveat=caveat,
        confidence=confidence,
        source_fields_used=source_fields,
        todo_verify=todo_verify,
    )


def rationale_to_dict(record: Mapping[str, Any] | Any) -> dict[str, Any]:
    return build_recommendation_rationale(record).to_dict()


def _field(record: Mapping[str, Any] | Any, *names: str) -> str:
    for name in names:
        value = record.get(name) if isinstance(record, Mapping) else getattr(record, name, None)
        if isinstance(value, str):
            cleaned = normalize_whitespace(value)
            if cleaned:
                return cleaned
    return ""


def _list_field(record: Mapping[str, Any] | Any, *names: str) -> list[str]:
    values: list[str] = []
    for name in names:
        raw = record.get(name) if isinstance(record, Mapping) else getattr(record, name, None)
        if isinstance(raw, str):
            values.extend(part.strip() for part in re.split(r"[,;]", raw) if part.strip())
        elif isinstance(raw, (list, tuple, set)):
            values.extend(str(item).strip() for item in raw if str(item).strip())
    return sorted(set(values), key=str.lower)


def _source_fields(**fields: Any) -> list[str]:
    used: list[str] = []
    for name, value in fields.items():
        if value:
            used.append(name)
    return used


def _evidence_basis(
    *,
    abstract: str,
    conclusion: str,
    notes: str,
    source: str,
    keywords: list[str],
    title: str,
) -> list[str]:
    basis: list[str] = []
    if conclusion:
        basis.append("conclusion-derived")
    if abstract:
        basis.append("abstract-derived")
    if notes:
        basis.append("repository-note-derived")
    if source or keywords:
        basis.append("metadata-derived")
    if title and not any([abstract, conclusion, notes]):
        basis.append("title-derived")
    return basis or ["insufficient-evidence"]


def _confidence(evidence_basis: list[str]) -> str:
    if "conclusion-derived" in evidence_basis:
        return "conclusion_supported"
    if "abstract-derived" in evidence_basis:
        return "abstract_supported"
    if "repository-note-derived" in evidence_basis:
        return "repository_note_supported"
    if "metadata-derived" in evidence_basis:
        return "metadata_supported"
    if "title-derived" in evidence_basis:
        return "title_only"
    return "insufficient_evidence"


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", normalize_whitespace(text))
    return [_clip(part, limit=240) for part in parts if part.strip()]


def _problem_summary(title: str, sentences: list[str]) -> str:
    if sentences:
        return f"从摘要看，论文关注的问题是：{sentences[0]}"
    if title:
        return f"摘要为空；仅能从标题判断主题为：{_clip(title)}"
    return "摘要为空且标题缺失，无法可靠概括问题。"


def _cue_summary(sentences: list[str], cues: tuple[str, ...], fallback: str) -> str:
    primary_cues = tuple(cue for cue in cues if cue not in {"study", "studies"})
    fallback_cues = tuple(cue for cue in cues if cue in {"study", "studies"})
    for cue_group in (primary_cues, fallback_cues):
        for sentence in sentences:
            lowered = sentence.lower()
            if any(cue in lowered for cue in cue_group):
                return sentence
    return fallback


def _matched_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    matches = [term for term in terms if term in lowered]
    return sorted(set(matches), key=str.lower)


def _radar_relevance(title: str, abstract: str, notes: str, keywords: list[str], relevant_terms: list[str]) -> str:
    combined = " ".join([title, abstract, notes, " ".join(keywords)]).lower()
    has_fhe = any(term in combined for term in ("fhe", "fully homomorphic", "homomorphic encryption", "ckks", "bfv", "bgv", "tfhe"))
    has_application = any(term in combined for term in APPLICATION_CUES)
    has_core = any(term in combined for term in ("lwe", "rlwe", "mlwe", "sis", "module-sis", "bkz", "ml-kem", "ml-dsa", "kyber", "dilithium"))
    has_core_analysis = any(term in combined for term in ("attack", "cryptanalysis", "parameter", "estimator", "security margin", "side-channel", "fault"))
    if has_fhe and has_application and not has_core_analysis:
        return "与雷达的 FHE/隐私计算背景线相关，但更像应用或系统论文；建议作为 peripheral/temporary track，而不是核心格攻击或参数估计论文。"
    if relevant_terms:
        terms = "、".join(relevant_terms[:8])
        return f"与格密码/PQC 雷达相关：可见证据包含 {terms}。"
    if has_fhe:
        return "与 FHE 背景可能相关，但缺少 LWE/RLWE/MLWE 或具体格方案证据；只应暂存并核验。"
    return "当前证据未显示明确格密码/PQC 锚点；不应仅因关键词进入核心阅读队列。"


def _recommendation_reason(*, title: str, confidence: str, radar_relevance: str, relevant_terms: list[str]) -> str:
    action = _reading_action(confidence, relevant_terms, radar_relevance)
    subject = _clip(title, limit=120) if title else "该记录"
    if confidence in {"abstract_supported", "conclusion_supported"}:
        return f"{action}：{subject} 的摘要/结论证据足以支持初步判断；{radar_relevance}"
    if confidence in {"metadata_supported", "repository_note_supported", "title_only"}:
        return f"{action}：{subject} 的证据仍偏元数据层面；{radar_relevance}"
    return f"暂存：{subject} 证据不足，需补齐摘要或来源元数据后再判断。"


def _reading_action(confidence: str, relevant_terms: list[str], radar_relevance: str) -> str:
    if "peripheral/temporary track" in radar_relevance:
        return "暂存"
    if confidence in {"abstract_supported", "conclusion_supported"} and relevant_terms:
        core_terms = {"lwe", "rlwe", "mlwe", "sis", "module-sis", "bkz", "ml-kem", "ml-dsa"}
        if core_terms.intersection({term.lower() for term in relevant_terms}):
            return "精读"
        return "扫读"
    if confidence in {"metadata_supported", "repository_note_supported", "title_only"}:
        return "暂存"
    return "忽略"


def _todo_verify(*, abstract: str, conclusion: str, relevant_terms: list[str]) -> list[str]:
    items: list[str] = []
    if not abstract:
        items.append("TODO_VERIFY: abstract is missing; method and contribution cannot be trusted.")
    if not conclusion:
        items.append("TODO_VERIFY: conclusion/full text not available; claims need paper-level verification.")
    if not relevant_terms:
        items.append("TODO_VERIFY: lattice/PQC relevance requires stronger evidence.")
    return items


def _caveat(confidence: str, *, abstract: str, conclusion: str, relevant_terms: list[str]) -> str:
    if confidence == "title_only":
        return "TODO_VERIFY：当前只有标题级证据，不能推断具体方法、贡献或安全结论。"
    if confidence == "metadata_supported":
        return "TODO_VERIFY：当前主要依赖关键词/来源元数据，关键词命中不能替代摘要或全文阅读。"
    if not abstract:
        return "TODO_VERIFY：摘要缺失，需回到来源页面确认问题、方法和贡献。"
    if not conclusion:
        return "TODO_VERIFY：未见结论或全文；证明细节、实验设置、参数和安全声明仍需核验。"
    if not relevant_terms:
        return "TODO_VERIFY：虽有文本证据，但格密码/PQC 关联仍不够明确。"
    return "TODO_VERIFY：仍需阅读正文核验证明、参数、实验和限制条件。"


def _only_keywords(keywords: list[str], notes: str) -> bool:
    if not notes:
        return True
    lowered = notes.lower()
    return bool(keywords) and ("matched keyword" in lowered or "命中" in lowered)


def _clip(value: str, limit: int = 220) -> str:
    text = normalize_whitespace(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
