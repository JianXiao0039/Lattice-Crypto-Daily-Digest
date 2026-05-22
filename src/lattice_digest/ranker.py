"""
Relevance ranker for lattice-cryptography paper monitoring.

This module assigns A/B/C/D labels to candidate papers.

Label semantics:
- A: Core lattice cryptography. Must include.
- B: Strongly related PQC/security/implementation involving lattice schemes. Include.
- C: Potential background. Include briefly.
- D: Irrelevant or false positive. Exclude.

The ranker is deliberately conservative:
- "lattice" alone is not enough.
- Non-cryptographic lattice papers must be filtered out.
- No paper without reliable source URL should enter the digest.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from lattice_digest.filters import negative_matches as config_negative_matches
from lattice_digest.filters import should_exclude_as_negative
from lattice_digest.models import PaperRecord, copy_record
from lattice_digest.text import combined_text, find_terms


@dataclass
class RankingResult:
    score: int
    label: str
    reading_priority: str
    matched_keywords: list[str] = field(default_factory=list)
    negative_keywords: list[str] = field(default_factory=list)
    taxonomy_tags: list[str] = field(default_factory=list)
    reason: str = ""


CORE_LATTICE_KEYWORDS: tuple[str, ...] = (
    "lwe",
    "learning with errors",
    "rlwe",
    "ring-lwe",
    "ring learning with errors",
    "mlwe",
    "module-lwe",
    "module learning with errors",
    "polynomial-lwe",
    "plwe",
    "tlwe",
    "lwr",
    "learning with rounding",
    "sis",
    "short integer solution",
    "msis",
    "module-sis",
    "isis",
    "inhomogeneous sis",
    "ring-sis",
    "ntru",
    "ntru lattice",
    "ntru problem",
    "ntru assumption",
    "svp",
    "shortest vector problem",
    "approximate svp",
    "usvp",
    "unique svp",
    "sivp",
    "cvp",
    "closest vector problem",
    "approximate cvp",
    "bdd",
    "bounded distance decoding",
    "gapsvp",
    "gapcvp",
    "minimax-cvp",
    "lattice decoding",
    "nearest plane",
    "embedding technique",
    "decoding attack",
    "bkz",
    "lll",
    "lattice reduction",
    "lattice sieving",
    "enumeration",
    "primal attack",
    "dual attack",
    "hybrid attack",
    "g6k",
    "fplll",
    "kyber",
    "ml-kem",
    "dilithium",
    "ml-dsa",
    "falcon",
    "fn-dsa",
    "frodokem",
    "saber",
    "newhope",
    "qtesla",
    "hawk",
    "haetae",
    "raccoon",
    "fully homomorphic encryption",
    "fhe",
    "ckks",
    "bfv",
    "bgv",
    "tfhe",
    "gsw",
    "gentry-sahai-waters",
)

AMBIGUOUS_CONTEXT_KEYWORDS: tuple[str, ...] = (
    "sis",
    "sivp",
    "lattice decoding",
    "nearest plane",
    "enumeration",
)

CRYPTO_CONTEXT_KEYWORDS: tuple[str, ...] = (
    "cryptography",
    "cryptographic",
    "cryptanalysis",
    "cryptanalytic",
    "post-quantum",
    "post quantum",
    "quantum-resistant",
    "quantum resistant",
    "quantum-safe",
    "quantum safe",
    "lattice-based",
    "kem",
    "key encapsulation",
    "signature",
    "digital signature",
    "encryption",
    "zero-knowledge",
    "zkp",
    "commitment",
    "homomorphic encryption",
    "side-channel",
    "side channel",
    "fault attack",
    "masking",
    "constant-time",
    "constant time",
    "secure implementation",
    "pqc",
    "nist pqc",
)

IMPLEMENTATION_KEYWORDS: tuple[str, ...] = (
    "ntt",
    "number theoretic transform",
    "polynomial multiplication",
    "modular multiplication",
    "modular reduction",
    "gaussian sampling",
    "discrete gaussian",
    "rejection sampling",
    "centered binomial sampling",
    "cdt sampler",
    "knuth-yao",
    "uniform sampling",
    "trapdoor",
    "lattice trapdoor generation",
    "constant-time",
    "constant time",
    "avx",
    "avx2",
    "avx512",
    "neon",
    "simd",
    "vectorization",
    "fpga",
    "asic",
    "risc-v",
    "cortex-m",
    "hls",
    "rtl",
    "verilog",
    "vhdl",
    "embedded implementation",
)

PHYSICAL_SECURITY_KEYWORDS: tuple[str, ...] = (
    "side-channel",
    "side channel",
    "power analysis",
    "timing attack",
    "cache attack",
    "electromagnetic",
    "template attack",
    "profiled attack",
    "deep-learning side-channel",
    "neural network side-channel",
    "cnn side-channel",
    "transformer side-channel",
    "fault attack",
    "fault injection",
    "laser fault injection",
    "voltage glitch",
    "clock glitch",
    "masking",
    "threshold masking",
    "countermeasure",
    "leakage resilience",
)

AI_LATTICE_KEYWORDS: tuple[str, ...] = (
    "machine learning lwe",
    "transformer lwe",
    "neural cryptanalysis",
    "ai-assisted lattice cryptanalysis",
    "learning-augmented cryptanalysis",
    "neural lattice reduction",
    "learning-guided bkz",
    "learned pruning",
    "coordinate selection",
    "modular arithmetic learning",
    "algorithmic reasoning",
    "algorithmic reasoning for cryptanalysis",
    "swin transformer",
    "salsa",
    "sparse lwe",
    "lwe benchmark",
    "stepwise regression",
    "data repetition",
)

HARD_NEGATIVE_KEYWORDS: tuple[str, ...] = (
    "crystal lattice",
    "crystalline lattice",
    "lattice qcd",
    "lattice quantum chromodynamics",
    "lattice boltzmann",
    "lattice boltzmann method",
    "spin lattice",
    "optical lattice",
    "solid-state lattice",
    "solid state lattice",
    "materials lattice",
    "material lattice",
    "lattice oxygen",
    "lattice thermal conductivity",
    "thermal conductivity lattice",
    "phonon lattice",
    "lattice vibration",
    "lattice dynamics",
    "lattice gauge theory",
    "lattice field theory",
    "lattice hamiltonian",
    "ising lattice",
    "hubbard lattice",
    "bravais lattice",
    "reciprocal lattice",
    "lattice constant",
    "lattice strain",
    "lattice defect",
    "lattice defects",
    "lattice mismatch",
    "lattice relaxation",
    "lattice symmetry",
    "lattice structure",
    "lattice site",
    "lattice gas",
    "lattice fluid",
    "protein lattice",
    "biological lattice",
    "molecular lattice",
    "supramolecular lattice",
    "polymer lattice",
    "enzyme lattice",
    "cell lattice",
    "lattice path",
    "distributive lattice",
    "boolean lattice",
    "lattice-ordered group",
    "lattice polytope",
    "lattice surgery",
    "surface code lattice",
    "quantum error correction lattice",
    "topological lattice model",
    "sis model",
    "nonlocal sis model",
    "susceptible infectious",
    "epidemic model",
    "epidemiological model",
    "logistic source",
    "dispersal kernels",
)

GENERIC_PQC_KEYWORDS: tuple[str, ...] = (
    "post-quantum cryptography",
    "post quantum cryptography",
    "pqc",
    "nist pqc",
    "quantum-safe",
    "quantum resistant",
    "quantum-resistant",
)

HIGH_VALUE_SOURCES: tuple[str, ...] = (
    "iacr eprint",
    "crypto",
    "eurocrypt",
    "asiacrypt",
    "pkc",
    "tcc",
    "ches",
    "tches",
    "fse",
    "tosc",
    "journal of cryptology",
    "pqcrypto",
)


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.lower()
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def phrase_in_text(phrase: str, text: str) -> bool:
    phrase = normalize_text(phrase)
    if not phrase:
        return False

    # Short acronyms should match as tokens.
    if len(phrase) <= 6 and re.fullmatch(r"[a-z0-9-]+", phrase):
        pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
        return re.search(pattern, text) is not None

    return phrase in text


def collect_matches(text: str, keywords: Iterable[str]) -> list[str]:
    matches: list[str] = []
    for kw in keywords:
        if phrase_in_text(kw, text):
            matches.append(kw)
    return sorted(set(matches), key=str.lower)


def has_any(text: str, keywords: Iterable[str]) -> bool:
    return bool(collect_matches(text, keywords))


def infer_label(score: int) -> tuple[str, str]:
    if score >= 80:
        return "A", "必读"
    if score >= 60:
        return "B", "值得跟踪"
    if score >= 40:
        return "C", "可选关注"
    return "D", "过滤"


def rank_paper(
    *,
    title: str,
    abstract: str = "",
    source: str = "",
    venue: str = "",
    url: str = "",
    taxonomy_matches: Mapping[str, Sequence[str]] | None = None,
) -> RankingResult:
    """
    Rank one candidate paper.

    Parameters
    ----------
    title:
        Paper title.
    abstract:
        Paper abstract.
    source:
        Data source, e.g. IACR ePrint, arXiv, DBLP.
    venue:
        Venue metadata if available.
    url:
        Reliable paper URL.
    taxonomy_matches:
        Optional mapping from taxonomy tag to matched keywords.

    Returns
    -------
    RankingResult
    """

    normalized_title = normalize_text(title)
    normalized_abstract = normalize_text(abstract)
    normalized_source = normalize_text(source)
    normalized_venue = normalize_text(venue)

    title_text = normalized_title
    abstract_text = normalized_abstract
    all_text = " ".join(
        part for part in [title_text, abstract_text, normalized_source, normalized_venue] if part
    )

    score = 0
    reasons: list[str] = []

    matched_keywords: list[str] = []
    negative_keywords: list[str] = []
    taxonomy_tags: list[str] = []

    if not url:
        return RankingResult(
            score=0,
            label="D",
            reading_priority="过滤",
            matched_keywords=[],
            negative_keywords=[],
            taxonomy_tags=[],
            reason="没有可靠 URL，按照 no hallucination 规则过滤。",
        )

    title_core = collect_matches(title_text, CORE_LATTICE_KEYWORDS)
    abstract_core = collect_matches(abstract_text, CORE_LATTICE_KEYWORDS)
    context_matches = collect_matches(all_text, CRYPTO_CONTEXT_KEYWORDS)
    implementation_matches = collect_matches(all_text, IMPLEMENTATION_KEYWORDS)
    physical_matches = collect_matches(all_text, PHYSICAL_SECURITY_KEYWORDS)
    ai_matches = collect_matches(all_text, AI_LATTICE_KEYWORDS)
    generic_pqc_matches = collect_matches(all_text, GENERIC_PQC_KEYWORDS)
    negative_matches = collect_matches(all_text, HARD_NEGATIVE_KEYWORDS)

    matched_keywords.extend(title_core)
    matched_keywords.extend(abstract_core)
    matched_keywords.extend(context_matches)
    matched_keywords.extend(implementation_matches)
    matched_keywords.extend(physical_matches)
    matched_keywords.extend(ai_matches)
    matched_keywords.extend(generic_pqc_matches)
    negative_keywords.extend(negative_matches)

    matched_keywords = sorted(set(matched_keywords), key=str.lower)
    negative_keywords = sorted(set(negative_keywords), key=str.lower)

    core_matches = sorted(set(title_core + abstract_core), key=str.lower)
    strong_core_matches = [
        kw for kw in core_matches if kw.lower() not in {item.lower() for item in AMBIGUOUS_CONTEXT_KEYWORDS}
    ]
    has_crypto_context = bool(context_matches or strong_core_matches)
    has_core_lattice = bool(title_core or abstract_core)

    if negative_matches and not has_crypto_context:
        return RankingResult(
            score=0,
            label="D",
            reading_priority="过滤",
            matched_keywords=matched_keywords,
            negative_keywords=negative_keywords,
            taxonomy_tags=[],
            reason=(
                "命中非密码学 lattice 负关键词，且没有密码学上下文。"
                f"负关键词：{', '.join(negative_matches)}。"
            ),
        )

    if has_core_lattice and not has_crypto_context:
        return RankingResult(
            score=20,
            label="D",
            reading_priority="过滤",
            matched_keywords=matched_keywords,
            negative_keywords=negative_keywords,
            taxonomy_tags=[],
            reason=(
                "仅命中 SIS/SIVP/enumeration 等可能歧义的格相关缩写，"
                "但没有 cryptography、cryptanalysis、post-quantum、LWE、NTRU、BKZ、FHE 等明确密码学上下文。"
            ),
        )

    # "lattice" alone is not enough.
    if "lattice" in all_text and not has_crypto_context and not has_core_lattice:
        return RankingResult(
            score=20,
            label="D",
            reading_priority="过滤",
            matched_keywords=matched_keywords,
            negative_keywords=negative_keywords,
            taxonomy_tags=[],
            reason="只出现 lattice，但没有密码学、PQC、LWE、SIS、NTRU、BKZ、FHE 等上下文。",
        )

    # Positive score.
    if title_core:
        score += 45
        reasons.append(f"标题命中核心格密码关键词：{', '.join(title_core)}。")

    if abstract_core:
        score += 30
        reasons.append(f"摘要命中核心格密码关键词：{', '.join(abstract_core[:8])}。")

    if context_matches:
        score += 15
        reasons.append("存在明确密码学/PQC上下文。")

    if implementation_matches:
        score += 15
        reasons.append(f"命中格密码实现相关关键词：{', '.join(implementation_matches[:8])}。")

    if physical_matches:
        score += 15
        reasons.append(f"命中物理安全相关关键词：{', '.join(physical_matches[:8])}。")

    if ai_matches and has_crypto_context:
        score += 15
        reasons.append(f"命中 AI 辅助密码分析相关关键词：{', '.join(ai_matches[:8])}。")
    elif ai_matches and not has_crypto_context:
        score -= 25
        reasons.append("命中 AI 关键词，但缺少密码学上下文，降低优先级。")

    if generic_pqc_matches and not has_core_lattice:
        score += 20
        reasons.append("命中通用 PQC 关键词，但尚未确认格基对象。")

    if any(phrase_in_text(src, normalized_source + " " + normalized_venue) for src in HIGH_VALUE_SOURCES):
        score += 20
        reasons.append("来源属于高价值密码学会议/期刊/数据库。")

    if taxonomy_matches:
        for tag, kws in taxonomy_matches.items():
            if kws:
                taxonomy_tags.append(tag)
                score += min(20, 5 * len(kws))
        if taxonomy_tags:
            reasons.append(f"命中 taxonomy 标签：{', '.join(taxonomy_tags[:8])}。")

    # Negative penalties.
    if negative_matches and has_crypto_context:
        score -= 30
        reasons.append(
            "虽然命中非密码学 lattice 负关键词，但也存在密码学上下文，因此扣分但不直接过滤。"
        )

    # Cap rules.
    if generic_pqc_matches and not has_core_lattice and not implementation_matches and not physical_matches:
        score = min(score, 75)
        reasons.append("通用 PQC 但没有明确格基方案，最高限制为 B 类。")

    if ai_matches and not has_core_lattice and not has_crypto_context:
        score = min(score, 45)
        reasons.append("AI/算法论文缺少明确格密码对象，最高限制为 C 类。")

    # If title and abstract contain no core lattice keywords, avoid over-ranking.
    if not has_core_lattice and not implementation_matches and not physical_matches:
        score = min(score, 65)

    score = max(0, min(100, score))
    label, priority = infer_label(score)

    if label == "D":
        priority = "过滤"

    if not reasons:
        reasons.append("未发现足够强的格密码相关证据。")

    return RankingResult(
        score=score,
        label=label,
        reading_priority=priority,
        matched_keywords=matched_keywords,
        negative_keywords=negative_keywords,
        taxonomy_tags=sorted(set(taxonomy_tags)),
        reason=" ".join(reasons),
    )


def rank_record(record: object) -> RankingResult:
    """
    Convenience wrapper for a PaperRecord-like object.

    The object is expected to have:
    - title
    - abstract
    - source
    - venue
    - source_url
    """

    return rank_paper(
        title=getattr(record, "title", ""),
        abstract=getattr(record, "abstract", ""),
        source=getattr(record, "source", ""),
        venue=getattr(record, "venue", ""),
        url=getattr(record, "source_url", "") or getattr(record, "url", ""),
    )


def _iter_taxonomy_items(taxonomy_config: Mapping[str, object]) -> Iterable[tuple[str, list[str]]]:
    legacy = taxonomy_config.get("taxonomy") if isinstance(taxonomy_config, dict) else None
    if isinstance(legacy, list):
        for item in legacy:
            if isinstance(item, dict):
                tag = str(item.get("tag", "unknown"))
                yield tag, [str(term) for term in item.get("terms", [])]
        return

    for group_name, group_value in taxonomy_config.items():
        if not isinstance(group_value, dict):
            continue
        for tag, item in group_value.items():
            if not isinstance(item, dict):
                continue
            keywords = item.get("keywords", [])
            if isinstance(keywords, list):
                yield str(tag), [str(term) for term in keywords]
            elif isinstance(keywords, str):
                yield str(tag), [keywords]


def taxonomy_matches(record: PaperRecord, taxonomy_config: Mapping[str, object]) -> dict[str, list[str]]:
    text = combined_text(record.title, record.abstract, record.venue, " ".join(record.categories))
    matches: dict[str, list[str]] = {}
    for tag, terms in _iter_taxonomy_items(taxonomy_config):
        found = find_terms(text, terms)
        if found:
            matches[tag] = found
    return matches


def _taxonomy_aliases(tags: Iterable[str]) -> list[str]:
    aliases: set[str] = set()
    for tag in tags:
        if tag.startswith("A"):
            aliases.add("lattice_reduction_cryptanalysis")
        elif tag.startswith("B"):
            aliases.add("lwe_sis_ntru_foundations")
        elif tag.startswith("C"):
            aliases.add("pqc_lattice_schemes")
        elif tag.startswith("D01"):
            aliases.add("fhe")
        elif tag.startswith("D02") or tag.startswith("D03") or tag.startswith("D04"):
            aliases.add("advanced_lattice_protocols")
        elif tag.startswith("E") or tag.startswith("F"):
            aliases.add("implementation_security")
        elif tag.startswith("G"):
            aliases.add("standardization_and_deployment")
        elif tag.startswith("H"):
            aliases.add("ai_assisted_lattice_cryptanalysis")
    return sorted(aliases)


def _priority_for_label(label: str) -> int:
    return {"A": 1, "B": 2, "C": 3}.get(label, 99)


def classify_record(
    record: PaperRecord,
    taxonomy_config: Mapping[str, object],
    keyword_config: Mapping[str, object],
    negative_config: Mapping[str, object],
) -> PaperRecord:
    taxonomy = taxonomy_matches(record, taxonomy_config)
    result = rank_paper(
        title=record.title,
        abstract=record.abstract,
        source=record.source,
        venue=record.venue or "",
        url=record.source_url,
        taxonomy_matches=taxonomy,
    )

    ranked = copy_record(record)
    config_negatives = config_negative_matches(record, dict(negative_config))
    should_exclude, exclude_terms = should_exclude_as_negative(
        record, dict(keyword_config), dict(negative_config)
    )

    label = result.label
    score = result.score
    reason = result.reason
    if should_exclude:
        label = "D"
        score = 0
        reason = (
            "命中 SKILL.md 定义的硬负关键词且缺少明确密码学上下文。"
            f"负关键词：{', '.join(exclude_terms)}。"
        )

    actual_tags = sorted(set(result.taxonomy_tags or taxonomy.keys()))
    aliases = _taxonomy_aliases(actual_tags)
    all_keywords = sorted(
        set(result.matched_keywords + [kw for values in taxonomy.values() for kw in values]),
        key=str.lower,
    )

    ranked.taxonomy_tags = sorted(set(actual_tags + aliases), key=str.lower)
    ranked.keywords_matched = all_keywords
    ranked.negative_keywords_matched = sorted(
        set(result.negative_keywords + config_negatives), key=str.lower
    )
    ranked.relevance_score = score
    ranked.relevance_label = label
    ranked.reading_priority = _priority_for_label(label)
    ranked.reason = reason
    return ranked


def rank_records(
    records: list[PaperRecord],
    taxonomy_config: Mapping[str, object],
    keyword_config: Mapping[str, object],
    negative_config: Mapping[str, object],
) -> list[PaperRecord]:
    return [
        classify_record(record, taxonomy_config, keyword_config, negative_config)
        for record in records
    ]
