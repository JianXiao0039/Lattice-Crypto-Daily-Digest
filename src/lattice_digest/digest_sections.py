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
GENERAL_CRYPTO_PRIVACY = "General Cryptography / Privacy"
OTHER_WATCHLIST = "Other / Watchlist"
IDEA_BANK_CANDIDATES = "Idea Bank Candidates"
PAPER_PLAN_CANDIDATES = "Paper Plan Candidates"
SOURCE_HEALTH_SUMMARY = "Source Health Summary"

TOPICAL_SECTION_ORDER: tuple[str, ...] = (
    LWE_FAMILY,
    SIS_NTRU_COMMITMENTS,
    LATTICE_REDUCTION_ATTACKS,
    PQC_STANDARDS,
    AI_LATTICE,
    IMPLEMENTATION_SYSTEMS,
    GENERAL_CRYPTO_PRIVACY,
    OTHER_WATCHLIST,
)
REPORT_BUCKET_ORDER: tuple[str, ...] = (
    HIGH_PRIORITY,
    IDEA_BANK_CANDIDATES,
    PAPER_PLAN_CANDIDATES,
)

# Backwards-compatible names used by older modules/tests. RESEARCH_SECTION_ORDER is
# intentionally topical-only after Phase 8D.1; PAPER_SECTION_ORDER is for display.
RESEARCH_SECTION_ORDER: tuple[str, ...] = TOPICAL_SECTION_ORDER
PAPER_SECTION_ORDER: tuple[str, ...] = (*REPORT_BUCKET_ORDER, *TOPICAL_SECTION_ORDER)
ALL_SECTION_ORDER: tuple[str, ...] = (*PAPER_SECTION_ORDER, SOURCE_HEALTH_SUMMARY)

LWE_EXPLICIT_TERMS = (
    "lwe",
    "learning with errors",
    "rlwe",
    "ring-lwe",
    "ring learning with errors",
    "mlwe",
    "module-lwe",
    "module learning with errors",
    "sparse lwe",
    "binary secret lwe",
    "ternary secret lwe",
    "small secret lwe",
)

SIS_NTRU_STRONG_TERMS = (
    "short integer solution",
    "module-sis",
    "ring-sis",
    "msis",
    "rsis",
    "ntru",
    "ntru lattice",
    "ntru lattices",
    "chameleon hash",
    "lattice commitment",
    "lattice-based commitment",
    "module-sis commitment",
    "module-sis chameleon hash",
)
SIS_WORD_TERMS = ("sis",)
COMMITMENT_WEAK_TERMS = ("commitment", "commitments", "trapdoor", "hash-and-sign")

REDUCTION_STRONG_TERMS = (
    "bkz",
    "g6k",
    "fplll",
    "fpylll",
    "lattice reduction",
    "lattice cryptanalysis",
    "lattice estimator",
    "primal attack",
    "dual attack",
    "hybrid attack",
    "secret recovery",
    "sparse secret recovery",
)
REDUCTION_CONTEXT_TERMS = (
    "lattice",
    "lwe",
    "rlwe",
    "mlwe",
    "sis",
    "ntru",
    "cryptanalysis",
    "attack",
    "security",
)
REDUCTION_WEAK_TERMS = ("lll", "svp", "cvp", "bdd", "sieving", "enumeration", "distinguisher", "distinguishing")

PQC_STRONG_TERMS = (
    "post-quantum",
    "pqc",
    "nist pqc",
    "fips 203",
    "fips 204",
    "fips 205",
    "ml-kem",
    "kyber",
    "crystals-kyber",
    "ml-dsa",
    "dilithium",
    "crystals-dilithium",
    "fn-dsa",
    "module-lattice kem",
    "module-lattice signature",
    "lattice-based signature",
    "lattice-based kem",
)
FALCON_FALSE_POSITIVE_PATTERNS = (
    "falcon-x",
    "falcon model",
    "falcon time series",
    "falcon foundation model",
    "time series foundation model",
)
FALCON_CONTEXT_TERMS = (
    "falcon signature",
    "falcon signing",
    "falcon verification",
    "falcon implementation",
    "falcon side-channel",
    "falcon fault",
    "fn-dsa",
    "post-quantum signature",
    "lattice-based signature",
    "nist pqc",
    "fips 205",
)
PQC_WEAK_TERMS = ("kem", "signature")

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
    "ml-guided",
    "learning-based",
)
AI_LATTICE_CONTEXT_TERMS = (
    "lattice cryptanalysis",
    "lattice reduction",
    "neural lattice reduction",
    "lwe",
    "rlwe",
    "mlwe",
    "module-lwe",
    "ring-lwe",
    "sis",
    "bkz",
    "lll",
    "hybrid attack",
    "primal attack",
    "dual attack",
    "cryptanalytic",
    "cryptanalysis",
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
    "hardware",
    "software",
    "production implementation",
    "audit",
    "auditing",
    "reduction placement",
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
)

GENERAL_CRYPTO_PRIVACY_TERMS = (
    "pir",
    "private information retrieval",
    "mpc",
    "multi-party computation",
    "multiparty computation",
    "anonymous two-party",
    "two-party computation",
    "privacy-preserving",
    "privacy preserving",
    "secure aggregation",
    "zero-knowledge",
    "zk",
    "anonymous credential",
    "secure computation",
    "gradient boosting decision tree",
    "gbdt",
)

CRYPTO_CONTEXT_TERMS = (
    "cryptography",
    "cryptographic",
    "cryptanalysis",
    "post-quantum",
    "pqc",
    "lattice",
    "lwe",
    "rlwe",
    "mlwe",
    "sis",
    "ntru",
    "kyber",
    "dilithium",
    "ml-kem",
    "ml-dsa",
    "falcon",
    "fn-dsa",
)

SIS_FALSE_CONTEXT_TERMS = (
    "susceptible",
    "epidemic",
    "epidemiology",
    "infection",
    "spreading",
)


def _order_map(order: tuple[str, ...]) -> dict[str, int]:
    return {value: index for index, value in enumerate(order)}


def _stable_unique(values: list[str], order: tuple[str, ...] = ALL_SECTION_ORDER) -> list[str]:
    ranks = _order_map(order)
    return sorted({value for value in values if value}, key=lambda item: (ranks.get(item, 999), item.lower()))


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
        if len(normalized) <= 8 and re.fullmatch(r"[a-z0-9+-]+", normalized):
            pattern = r"(?<![a-z0-9])" + re.escape(normalized) + r"(?![a-z0-9])"
            if re.search(pattern, text):
                return True
        elif normalized in text:
            return True
    return False


def _has_falcon_pqc_context(text: str) -> bool:
    if _has(text, FALCON_FALSE_POSITIVE_PATTERNS):
        return False
    return _has(text, FALCON_CONTEXT_TERMS)


def _has_lwe(text: str) -> bool:
    return _has(text, LWE_EXPLICIT_TERMS)


def _has_sis_ntru(text: str) -> bool:
    if _has(text, SIS_FALSE_CONTEXT_TERMS):
        return False
    if _has(text, SIS_NTRU_STRONG_TERMS):
        return True
    if _has(text, SIS_WORD_TERMS) and _has(text, CRYPTO_CONTEXT_TERMS):
        return True
    if _has(text, COMMITMENT_WEAK_TERMS) and _has(text, ("lattice", "module-sis", "sis", "post-quantum", "pqc", "ntru")):
        return True
    return False


def _has_reduction_attack(text: str) -> bool:
    if _has(text, REDUCTION_STRONG_TERMS):
        return True
    return _has(text, REDUCTION_WEAK_TERMS) and _has(text, REDUCTION_CONTEXT_TERMS)


def _has_pqc(text: str) -> bool:
    if _has(text, PQC_STRONG_TERMS):
        return True
    if _has_falcon_pqc_context(text):
        return True
    return _has(text, PQC_WEAK_TERMS) and _has(text, ("post-quantum", "pqc", "lattice-based", "module-lattice", "nist"))


def _has_ai_lattice(text: str) -> bool:
    return "ai-assisted lattice cryptanalysis" in text or (_has(text, AI_TERMS) and _has(text, AI_LATTICE_CONTEXT_TERMS))


def _has_general_crypto_privacy(text: str) -> bool:
    return _has(text, GENERAL_CRYPTO_PRIVACY_TERMS)


def _is_include_label(record: PaperRecord) -> bool:
    return record.relevance_label in {"A", "B", "C"}


def _is_high_priority(record: PaperRecord) -> bool:
    return record.relevance_label == "A" or record.relevance_score >= 80


def assign_research_sections(record: PaperRecord) -> list[str]:
    text = _text(record)
    sections: list[str] = []
    if _has_lwe(text):
        sections.append(LWE_FAMILY)
    if _has_sis_ntru(text):
        sections.append(SIS_NTRU_COMMITMENTS)
    if _has_reduction_attack(text):
        sections.append(LATTICE_REDUCTION_ATTACKS)
    if _has_pqc(text):
        sections.append(PQC_STANDARDS)
    if _has_ai_lattice(text):
        sections.append(AI_LATTICE)
    if _has(text, IMPLEMENTATION_TERMS):
        sections.append(IMPLEMENTATION_SYSTEMS)
    if _has_general_crypto_privacy(text):
        sections.append(GENERAL_CRYPTO_PRIVACY)
    if _is_include_label(record) and not sections:
        sections.append(OTHER_WATCHLIST)
    return _stable_unique(sections, TOPICAL_SECTION_ORDER)


def is_idea_bank_candidate(record: PaperRecord) -> bool:
    if not _is_include_label(record) or record.relevance_score < 60:
        return False
    sections = set(assign_research_sections(record))
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
    sections = set(assign_research_sections(record))
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


def assign_report_buckets(record: PaperRecord) -> list[str]:
    buckets: list[str] = []
    if _is_high_priority(record):
        buckets.append(HIGH_PRIORITY)
    if is_idea_bank_candidate(record):
        buckets.append(IDEA_BANK_CANDIDATES)
    if is_paper_plan_candidate(record):
        buckets.append(PAPER_PLAN_CANDIDATES)
    return _stable_unique(buckets, REPORT_BUCKET_ORDER)


def candidate_reason(record: PaperRecord, section: str) -> str:
    sections = set(assign_research_sections(record))
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


def sectioned_records(records: list[PaperRecord]) -> dict[str, list[PaperRecord]]:
    result = {section: [] for section in PAPER_SECTION_ORDER}
    for record in records:
        for bucket in assign_report_buckets(record):
            result[bucket].append(record)
        for section in assign_research_sections(record):
            result[section].append(record)
    return result
