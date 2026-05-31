from __future__ import annotations

import re

from lattice_digest.models import PaperRecord


HIGH_PRIORITY = "High-Priority Papers"
LWE_FAMILY = "LWE / RLWE / MLWE"
SIS_NTRU_COMMITMENTS = "SIS / NTRU / Commitments / Chameleon Hash"
LATTICE_REDUCTION_ATTACKS = "BKZ / LLL / G6K / Lattice Reduction / Attacks"
PQC_STANDARDS = "PQC Standards / ML-KEM / ML-DSA / Falcon"
AI_LATTICE = "AI-assisted Lattice Cryptanalysis"
IMPLEMENTATION_SYSTEMS = "Implementation / Side-channel / Systems"
IDEA_BANK_CANDIDATES = "Idea Bank Candidates"
PAPER_PLAN_CANDIDATES = "Paper Plan Candidates"
SOURCE_HEALTH_SUMMARY = "Source Health Summary"

RESEARCH_SECTION_ORDER: tuple[str, ...] = (
    HIGH_PRIORITY,
    LWE_FAMILY,
    SIS_NTRU_COMMITMENTS,
    LATTICE_REDUCTION_ATTACKS,
    PQC_STANDARDS,
    AI_LATTICE,
    IMPLEMENTATION_SYSTEMS,
    IDEA_BANK_CANDIDATES,
    PAPER_PLAN_CANDIDATES,
    SOURCE_HEALTH_SUMMARY,
)

PAPER_SECTION_ORDER: tuple[str, ...] = tuple(
    section for section in RESEARCH_SECTION_ORDER if section != SOURCE_HEALTH_SUMMARY
)

LWE_TERMS = (
    "lwe",
    "learning with errors",
    "rlwe",
    "ring-lwe",
    "ring learning with errors",
    "mlwe",
    "module-lwe",
    "module learning with errors",
    "sparse lwe",
    "binary secret",
    "ternary secret",
    "small secret",
)

SIS_NTRU_TERMS = (
    "sis",
    "short integer solution",
    "module-sis",
    "ring-sis",
    "msis",
    "rsis",
    "ntru",
    "commitment",
    "commitments",
    "chameleon hash",
    "trapdoor",
    "hash-and-sign",
)

REDUCTION_ATTACK_TERMS = (
    "bkz",
    "lll",
    "g6k",
    "fplll",
    "fpylll",
    "lattice reduction",
    "svp",
    "cvp",
    "bdd",
    "sieving",
    "enumeration",
    "primal attack",
    "dual attack",
    "hybrid attack",
    "lattice estimator",
    "secret recovery",
    "distinguisher",
    "distinguishing",
)

PQC_TERMS = (
    "post-quantum",
    "pqc",
    "nist pqc",
    "ml-kem",
    "kyber",
    "crystals-kyber",
    "ml-dsa",
    "dilithium",
    "crystals-dilithium",
    "falcon",
    "fn-dsa",
    "module-lattice",
    "kem",
    "signature",
)

AI_TERMS = (
    "ai-assisted",
    "machine learning",
    "deep learning",
    "neural",
    "transformer",
    "swin",
    "gnn",
    "graph neural",
    "reinforcement learning",
    "learning-augmented",
    "learned pruning",
    "coordinate selection",
    "candidate ranking",
    "neural lattice reduction",
)

AI_CRYPTO_CONTEXT_TERMS = (
    "lattice",
    "cryptanalysis",
    "cryptographic",
    "lwe",
    "rlwe",
    "mlwe",
    "sis",
    "bkz",
    "lll",
    "hybrid attack",
    "primal attack",
    "dual attack",
)

IMPLEMENTATION_TERMS = (
    "implementation",
    "implementations",
    "side-channel",
    "side channel",
    "fault",
    "fault attack",
    "constant-time",
    "constant time",
    "timing",
    "cache attack",
    "power analysis",
    "leakage",
    "masking",
    "ntt",
    "number theoretic transform",
    "avx",
    "neon",
    "risc-v",
    "embedded",
    "tls",
    "liboqs",
    "openssl",
    "benchmark",
    "audit",
)


def _stable_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value}, key=lambda item: RESEARCH_SECTION_ORDER.index(item))


def _text(record: PaperRecord) -> str:
    return " ".join(
        [
            record.title,
            record.abstract,
            record.source,
            record.venue or "",
            " ".join(record.categories),
            " ".join(record.keywords_matched),
            " ".join(record.taxonomy_tags),
            record.reason,
        ]
    ).lower()


def _has(text: str, terms: tuple[str, ...]) -> bool:
    for term in terms:
        normalized = term.lower()
        if len(normalized) <= 6 and re.fullmatch(r"[a-z0-9-]+", normalized):
            pattern = r"(?<![a-z0-9])" + re.escape(normalized) + r"(?![a-z0-9])"
            if re.search(pattern, text):
                return True
        elif normalized in text:
            return True
    return False


def _is_include_label(record: PaperRecord) -> bool:
    return record.relevance_label in {"A", "B", "C"}


def _is_high_priority(record: PaperRecord) -> bool:
    return record.relevance_label == "A" or record.relevance_score >= 80


def is_idea_bank_candidate(record: PaperRecord) -> bool:
    if not _is_include_label(record) or record.relevance_score < 60:
        return False
    sections = set(assign_research_sections(record, include_candidates=False))
    return bool(
        sections
        & {
            LWE_FAMILY,
            SIS_NTRU_COMMITMENTS,
            LATTICE_REDUCTION_ATTACKS,
            PQC_STANDARDS,
            AI_LATTICE,
            IMPLEMENTATION_SYSTEMS,
        }
    )


def is_paper_plan_candidate(record: PaperRecord) -> bool:
    if record.relevance_label not in {"A", "B"} or record.relevance_score < 75:
        return False
    sections = set(assign_research_sections(record, include_candidates=False))
    return bool(
        sections
        & {
            AI_LATTICE,
            LWE_FAMILY,
            SIS_NTRU_COMMITMENTS,
            LATTICE_REDUCTION_ATTACKS,
            IMPLEMENTATION_SYSTEMS,
        }
    )


def candidate_reason(record: PaperRecord, section: str) -> str:
    sections = set(assign_research_sections(record, include_candidates=False))
    if section == IDEA_BANK_CANDIDATES:
        if AI_LATTICE in sections:
            return "命中 AI4Lattice / lattice cryptanalysis 主线，可作为 idea bank 候选记录。"
        if SIS_NTRU_COMMITMENTS in sections:
            return "命中 SIS/NTRU/commitment/chameleon hash，可作为小原语 idea 候选。"
        if LATTICE_REDUCTION_ATTACKS in sections:
            return "命中 BKZ/LLL/G6K 或经典攻击，可沉淀为实验或 baseline idea。"
        if IMPLEMENTATION_SYSTEMS in sections:
            return "命中实现安全/侧信道/系统方向，可作为 PQC 落地安全线索。"
        return "相关性达到候选阈值，可先保留为研究线索。"
    if section == PAPER_PLAN_CANDIDATES:
        if SIS_NTRU_COMMITMENTS in sections:
            return "满足较高相关性，且贴近 Module-SIS/chameleon hash/commitment 短期论文规划。"
        if AI_LATTICE in sections:
            return "满足较高相关性，且可转化为 AI-assisted lattice cryptanalysis 子程序计划。"
        if LATTICE_REDUCTION_ATTACKS in sections:
            return "满足较高相关性，且可支撑可复现攻击 baseline 或参数实验计划。"
        return "满足较高相关性，适合进入 paper plan 候选池，但需人工核验贡献边界。"
    return "由标题、摘要、关键词或 taxonomy 的确定性匹配分入该研究板块。"


def assign_research_sections(record: PaperRecord, include_candidates: bool = True) -> list[str]:
    text = _text(record)
    sections: list[str] = []
    if _is_high_priority(record):
        sections.append(HIGH_PRIORITY)
    if _has(text, LWE_TERMS):
        sections.append(LWE_FAMILY)
    if _has(text, SIS_NTRU_TERMS):
        sections.append(SIS_NTRU_COMMITMENTS)
    if _has(text, REDUCTION_ATTACK_TERMS):
        sections.append(LATTICE_REDUCTION_ATTACKS)
    if _has(text, PQC_TERMS):
        sections.append(PQC_STANDARDS)
    if "ai-assisted lattice cryptanalysis" in text or (
        _has(text, AI_TERMS) and _has(text, AI_CRYPTO_CONTEXT_TERMS)
    ):
        sections.append(AI_LATTICE)
    if _has(text, IMPLEMENTATION_TERMS):
        sections.append(IMPLEMENTATION_SYSTEMS)
    if include_candidates and is_idea_bank_candidate(record):
        sections.append(IDEA_BANK_CANDIDATES)
    if include_candidates and is_paper_plan_candidate(record):
        sections.append(PAPER_PLAN_CANDIDATES)
    return _stable_unique(sections)


def sectioned_records(records: list[PaperRecord]) -> dict[str, list[PaperRecord]]:
    result = {section: [] for section in PAPER_SECTION_ORDER}
    for record in records:
        for section in assign_research_sections(record):
            result[section].append(record)
    return result
