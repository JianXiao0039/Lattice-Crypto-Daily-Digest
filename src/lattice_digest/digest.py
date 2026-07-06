from __future__ import annotations

from collections import Counter
from datetime import date

from lattice_digest.digest_sections import (
    IDEA_BANK_CANDIDATES,
    PAPER_PLAN_CANDIDATES,
    PAPER_SECTION_ORDER,
    SOURCE_HEALTH_SUMMARY,
    candidate_reason,
    sectioned_records,
)
from lattice_digest.models import PaperRecord
from lattice_digest.radar_freshness import apply_daily_freshness_policy
from lattice_digest.ranking_explainability import concise_ranking_explanation
from lattice_digest.recommendation_calibration import TODO_VERIFY, has_calibrated_recommendation
from lattice_digest.recommendation_rationale import build_recommendation_rationale
from lattice_digest.report_quality import (
    anchor_evidence_text,
    false_positive_risk_text,
    semantic_scholar_advisory_text,
    source_health_caveat_text,
)


TOPIC_TERMS: dict[str, tuple[str, ...]] = {
    "LWE": ("lwe", "learning with errors"),
    "RLWE": ("rlwe", "ring-lwe", "ring learning with errors"),
    "MLWE": ("mlwe", "module-lwe", "module learning with errors"),
    "ML-KEM": ("ml-kem", "kyber", "crystals-kyber"),
    "SIS": ("sis", "short integer solution"),
    "Module-SIS": ("module-sis", "msis", "module lattice"),
    "ML-DSA": ("ml-dsa", "dilithium", "crystals-dilithium"),
    "Falcon": ("falcon", "fn-dsa"),
    "Commitments": ("commitment", "commitments", "chameleon hash"),
    "Lattice Reduction": ("lattice reduction", "bkz", "lll", "svp", "cvp", "bdd"),
    "Cryptanalysis": ("cryptanalysis", "primal attack", "dual attack", "hybrid attack", "secret recovery"),
    "AI4Lattice": (
        "ai-assisted",
        "machine learning lwe",
        "transformer lwe",
        "neural lattice reduction",
        "learned pruning",
        "coordinate selection",
        "swin transformer",
    ),
    "FHE": ("fhe", "fully homomorphic encryption", "ckks", "bfv", "bgv", "tfhe", "bootstrapping"),
    "PQC Implementation": ("implementation", "side-channel", "fault", "constant-time", "ntt", "risc-v", "fpga"),
}

SECTION_TERMS: dict[str, tuple[str, ...]] = {
    "lwe_mlwe": (
        "lwe",
        "learning with errors",
        "rlwe",
        "ring-lwe",
        "mlwe",
        "module-lwe",
        "kyber",
        "ml-kem",
        "kem security",
        "fo transform",
        "primal attack",
        "dual attack",
        "hybrid attack",
    ),
    "sis_signatures": (
        "sis",
        "short integer solution",
        "module-sis",
        "msis",
        "ml-dsa",
        "dilithium",
        "falcon",
        "fn-dsa",
        "commitment",
        "chameleon hash",
        "signature",
        "trapdoor",
        "rejection sampling",
    ),
    "reduction": (
        "lll",
        "bkz",
        "svp",
        "cvp",
        "bdd",
        "enumeration",
        "sieving",
        "g6k",
        "fplll",
        "lattice estimator",
        "primal attack",
        "dual attack",
        "hybrid attack",
        "sparse lwe",
        "secret recovery",
        "distinguishing",
    ),
    "ai4lattice": TOPIC_TERMS["AI4Lattice"],
    "fhe_pqc": (
        "fhe",
        "fully homomorphic encryption",
        "ckks",
        "bfv",
        "bgv",
        "tfhe",
        "bootstrapping",
        "ntru",
        "post-quantum",
        "pqc",
        "side-channel",
        "fault",
    ),
}

ACTION_LABELS = {
    "Read today": "今日精读",
    "Read this week": "本周阅读",
    "Skim for related work": "略读作为 related work",
    "Save for background": "暂存",
    "Ignore unless needed": "暂不阅读",
    "TODO_VERIFY before reading": "先核验来源",
}

ACTION_BY_PRIORITY_LABEL = {
    "必须精读": "Read today",
    "建议精读": "Read this week",
    "可略读": "Skim for related work",
    "暂存": "Save for background",
    "低相关": "Ignore unless needed",
}

PRIORITY_RULES: tuple[tuple[str, tuple[str, ...], int, str], ...] = (
    (
        "AI-assisted lattice cryptanalysis",
        (
            "ai-assisted lattice cryptanalysis",
            "learning-assisted cryptanalysis",
            "neural cryptanalysis",
            "machine learning attacks on lwe",
            "machine learning lwe",
            "deep learning lwe",
            "learned pruning",
            "coordinate selection",
            "candidate ranking",
            "neural sieving",
        ),
        30,
        "直接贴近 AI-assisted lattice cryptanalysis，可优先判断它是否能作为经典攻击子程序。",
    ),
    (
        "Transformer/Swin/neural LWE",
        (
            "transformer lwe",
            "swin transformer",
            "swin-guided",
            "neural lattice reduction",
            "neural reduction",
            "ml-guided bkz",
            "reinforcement learning bkz",
            "graph neural network lattice reduction",
        ),
        28,
        "命中 Transformer/Swin/neural lattice reduction 主线，适合服务 Swin-guided coordinate selection 或神经格约简实验。",
    ),
    (
        "LWE/RLWE/MLWE attacks",
        (
            "lwe",
            "learning with errors",
            "rlwe",
            "ring-lwe",
            "mlwe",
            "module-lwe",
            "sparse lwe",
            "secret recovery",
            "distinguishing attack",
        ),
        26,
        "覆盖 LWE/RLWE/MLWE 或 sparse LWE 攻击，是当前安全分析和实验主线的核心素材。",
    ),
    (
        "primal/dual/hybrid attack",
        (
            "primal attack",
            "primal attacks",
            "dual attack",
            "dual attacks",
            "hybrid attack",
            "hybrid attacks",
            "bdd attack",
            "distinguishing attack",
            "secret recovery",
            "lattice reduction attack",
        ),
        22,
        "涉及 primal/dual/hybrid 等经典攻击接口，适合转化为参数估计或可复现实验。",
    ),
    (
        "BKZ/LLL/G6K/fplll/sieving",
        (
            "bkz",
            "lll",
            "g6k",
            "fplll",
            "sieving",
            "enumeration",
            "lattice reduction",
            "lattice estimator",
            "root hermite factor",
        ),
        20,
        "命中 BKZ/LLL/G6K/fplll/sieving 方向，可作为 lattice reduction 或攻击成本 baseline。",
    ),
    (
        "Module-SIS/commitment/chameleon hash",
        (
            "module-sis",
            "msis",
            "short integer solution",
            "commitment",
            "commitments",
            "chameleon hash",
            "lattice-based commitment",
            "trapdoor",
            "rejection sampling",
        ),
        24,
        "贴近 Module-SIS、承诺或 chameleon hash 小原语方向，可用于导师讨论和短论文选题判断。",
    ),
    (
        "ML-KEM/Kyber security and implementation",
        (
            "ml-kem",
            "kyber",
            "crystals-kyber",
            "kem security",
            "decapsulation failure",
            "side-channel",
            "fault attack",
            "implementation attack",
        ),
        23,
        "服务 ML-KEM/Kyber 安全、实现、侧信道或故障攻击线，适合纳入 PQC 实验与部署讨论。",
    ),
    (
        "ML-DSA/Dilithium/Falcon signatures",
        (
            "ml-dsa",
            "dilithium",
            "crystals-dilithium",
            "falcon",
            "fn-dsa",
            "lattice-based signature",
            "post-quantum signatures",
        ),
        21,
        "关联 ML-DSA/Dilithium/Falcon 或格签名，可用于签名安全、实现或参数化背景。",
    ),
    (
        "FHE and lattice HE",
        (
            "fhe",
            "fully homomorphic encryption",
            "ckks",
            "bfv",
            "bgv",
            "tfhe",
            "bootstrapping",
            "lattice-based homomorphic encryption",
        ),
        10,
        "属于格密码中的 FHE/HE 扩展方向，通常作为背景扩展或工程优化线索。",
    ),
    (
        "broader PQC implementation and standardization",
        (
            "post-quantum cryptography",
            "pqc",
            "nist pqc",
            "standardization",
            "deployment",
            "quantum-safe",
            "post-quantum tls",
        ),
        4,
        "属于 broader PQC 标准化或部署背景，除非明确连接格方案，否则精读优先级较低。",
    ),
)

PRIORITY_TIE_RANK = {
    "AI-assisted lattice cryptanalysis": 1,
    "Transformer/Swin/neural LWE": 1,
    "LWE/RLWE/MLWE attacks": 2,
    "primal/dual/hybrid attack": 3,
    "BKZ/LLL/G6K/fplll/sieving": 4,
    "Module-SIS/commitment/chameleon hash": 5,
    "ML-KEM/Kyber security and implementation": 6,
    "ML-DSA/Dilithium/Falcon signatures": 6,
    "FHE and lattice HE": 7,
    "broader PQC implementation and standardization": 8,
}

CRYPTO_CONTEXT_TERMS = (
    "lattice",
    "lattices",
    "cryptanalysis",
    "cryptographic",
    "cryptography",
    "lwe",
    "rlwe",
    "mlwe",
    "module-lwe",
    "sis",
    "module-sis",
    "ntru",
    "bkz",
    "lll",
    "svp",
    "cvp",
    "bdd",
    "kyber",
    "ml-kem",
    "dilithium",
    "ml-dsa",
    "falcon",
    "fhe",
    "homomorphic encryption",
)

ATTACK_CONTEXT_TERMS = (
    "attack",
    "attacks",
    "cryptanalysis",
    "security estimate",
    "security analysis",
    "cost model",
    "secret recovery",
    "distinguishing",
    "bkz",
    "lll",
    "primal attack",
    "dual attack",
    "hybrid attack",
    "lattice estimator",
    "reduction",
)

SPECIFIC_SCHEME_TERMS = (
    "ml-kem",
    "kyber",
    "crystals-kyber",
    "ml-dsa",
    "dilithium",
    "crystals-dilithium",
    "falcon",
    "fn-dsa",
)

IMPLEMENTATION_RISK_TERMS = (
    "side-channel",
    "fault",
    "fault attack",
    "leakage",
    "vulnerability",
    "failure",
    "audit",
    "constant-time",
    "masking",
    "production",
    "implementation attack",
    "security",
)

PRIORITY_LABELS: tuple[tuple[int, str], ...] = (
    (85, "必须精读"),
    (70, "建议精读"),
    (50, "可略读"),
    (30, "暂存"),
    (0, "低相关"),
)


def _combined_text(record: PaperRecord) -> str:
    return " ".join(
        [
            record.title,
            record.abstract,
            record.venue or "",
            " ".join(record.categories),
            " ".join(record.taxonomy_tags),
            " ".join(record.keywords_matched),
        ]
    ).lower()


def _matches(record: PaperRecord, terms: tuple[str, ...]) -> bool:
    text = _combined_text(record)
    return any(term.lower() in text for term in terms)


def _matches_text(text: str, terms: tuple[str, ...]) -> bool:
    return any(term.lower() in text for term in terms)


def research_tags(record: PaperRecord) -> list[str]:
    tags = [tag for tag, terms in TOPIC_TERMS.items() if _matches(record, terms)]
    return tags or list(record.taxonomy_tags[:3]) or list(record.keywords_matched[:3])


def suggested_action(record: PaperRecord) -> str:
    if has_calibrated_recommendation(record) and record.suggested_action:
        return record.suggested_action
    return ACTION_BY_PRIORITY_LABEL[priority_label(record)]


def _action_text(record: PaperRecord) -> str:
    action = suggested_action(record)
    return ACTION_LABELS.get(action, action)


def _title_text(record: PaperRecord) -> str:
    return record.title.lower()


def _abstract_text(record: PaperRecord) -> str:
    return record.abstract.lower()


def _content_text(record: PaperRecord) -> str:
    return " ".join([record.title, record.abstract]).lower()


def _has_any_hit(record: PaperRecord, terms: tuple[str, ...]) -> bool:
    return _matches_text(_combined_text(record), terms)


def _has_content_hit(record: PaperRecord, terms: tuple[str, ...]) -> bool:
    return _matches_text(_content_text(record), terms)


def _has_title_hit(record: PaperRecord, terms: tuple[str, ...]) -> bool:
    return _matches_text(_title_text(record), terms)


def _has_abstract_hit(record: PaperRecord, terms: tuple[str, ...]) -> bool:
    return _matches_text(_abstract_text(record), terms)


def _has_crypto_context(record: PaperRecord) -> bool:
    return _has_any_hit(record, CRYPTO_CONTEXT_TERMS)


def _has_attack_context(record: PaperRecord) -> bool:
    return _has_any_hit(record, ATTACK_CONTEXT_TERMS)


def _has_specific_scheme(record: PaperRecord) -> bool:
    return _has_any_hit(record, SPECIFIC_SCHEME_TERMS)


def _has_implementation_risk(record: PaperRecord) -> bool:
    return _has_any_hit(record, IMPLEMENTATION_RISK_TERMS)


def _priority_hits(record: PaperRecord) -> list[tuple[str, int, str]]:
    text = _combined_text(record)
    hits: list[tuple[str, int, str]] = []
    for name, terms, weight, reason in PRIORITY_RULES:
        if name in {"AI-assisted lattice cryptanalysis", "Transformer/Swin/neural LWE"}:
            if _matches_text(text, terms) and _has_crypto_context(record):
                hits.append((name, weight, reason))
            continue
        if name == "LWE/RLWE/MLWE attacks":
            has_lwe_family = _matches_text(
                text,
                (
                    "lwe",
                    "learning with errors",
                    "rlwe",
                    "ring-lwe",
                    "mlwe",
                    "module-lwe",
                    "sparse lwe",
                ),
            )
            if has_lwe_family and _has_attack_context(record):
                hits.append((name, weight, reason))
            continue
        if name == "primal/dual/hybrid attack":
            if _matches_text(text, terms) and _has_crypto_context(record):
                hits.append((name, weight, reason))
            continue
        if name == "ML-KEM/Kyber security and implementation":
            has_scheme = _matches_text(text, ("ml-kem", "kyber", "crystals-kyber"))
            if has_scheme or (_matches_text(text, terms) and _has_specific_scheme(record) and _has_implementation_risk(record)):
                hits.append((name, weight, reason))
            continue
        if name == "ML-DSA/Dilithium/Falcon signatures":
            has_scheme = _matches_text(text, ("ml-dsa", "dilithium", "crystals-dilithium", "falcon", "fn-dsa"))
            has_signature_context = _matches_text(text, ("signature", "signatures", "implementation", "side-channel", "fault", "security"))
            if has_scheme or (_matches_text(text, terms) and has_signature_context):
                hits.append((name, weight, reason))
            continue
        if _matches_text(text, terms):
            hits.append((name, weight, reason))
    return hits


def reading_priority_score(record: PaperRecord) -> int:
    if has_calibrated_recommendation(record):
        return max(0, min(100, int(record.recommendation_score or 0)))
    label_base = {"A": 22, "B": 16, "C": 8}.get(record.relevance_label, 0)
    score = label_base + max(0, min(record.relevance_score, 100)) // 5
    hits = _priority_hits(record)
    weighted_hits = sorted(hits, key=lambda hit: PRIORITY_TIE_RANK.get(hit[0], 99))
    for index, (_, weight, _) in enumerate(weighted_hits[:4]):
        if index == 0:
            score += weight
        elif index == 1:
            score += round(weight * 0.45)
        elif index == 2:
            score += round(weight * 0.25)
        else:
            score += round(weight * 0.1)

    if any(_has_title_hit(record, terms) for _, terms, _, _ in PRIORITY_RULES):
        score += 4
    if any(_has_abstract_hit(record, terms) for _, terms, _, _ in PRIORITY_RULES):
        score += 3
    if record.source.lower().split(",")[0].strip() in {"iacr_eprint", "arxiv"}:
        score += 2

    cap = _priority_score_cap(record, hits)
    score = min(score, cap)
    if not record.source_url:
        score -= 20
        score = min(score, 49)
    if record.relevance_label == "D":
        score = min(score, 29)
    return max(0, min(100, score))


def _priority_score_cap(record: PaperRecord, hits: list[tuple[str, int, str]]) -> int:
    text = _combined_text(record)
    content = _content_text(record)
    hit_names = {name for name, _, _ in hits}
    has_top_core = bool(
        hit_names
        & {
            "AI-assisted lattice cryptanalysis",
            "Transformer/Swin/neural LWE",
            "LWE/RLWE/MLWE attacks",
            "primal/dual/hybrid attack",
            "BKZ/LLL/G6K/fplll/sieving",
        }
    )
    cap = 98
    if not record.abstract.strip():
        cap = min(cap, 84)
    if hits and not any(
        _matches_text(content, terms)
        for name, terms, _, _ in PRIORITY_RULES
        if name in hit_names
    ):
        cap = min(cap, 69)
    if hits and any(_has_title_hit(record, terms) for name, terms, _, _ in PRIORITY_RULES if name in hit_names) and not any(
        _has_abstract_hit(record, terms)
        for name, terms, _, _ in PRIORITY_RULES
        if name in hit_names
    ):
        cap = min(cap, 84)
    if _matches_text(text, ("survey", "overview", "introduction", "tutorial")) and not has_top_core:
        cap = min(cap, 75)
    if "broader PQC implementation and standardization" in hit_names and not (
        has_top_core or _has_specific_scheme(record)
    ):
        cap = min(cap, 60)
    if _is_fhe_application(record, hit_names):
        cap = min(cap, 65)
    if _is_weak_implementation_audit(record):
        cap = min(cap, 75)
    if _matches_text(text, ("quantum attack", "quantum attacks", "quantum algorithm")) and not has_top_core:
        cap = min(cap, 88)
    if _only_generic_lattice_or_lwe(record, hit_names):
        cap = min(cap, 49)
    return cap


def _is_fhe_application(record: PaperRecord, hit_names: set[str]) -> bool:
    if "FHE and lattice HE" not in hit_names:
        return False
    content = _content_text(record)
    has_direct_security_or_parameter = _matches_text(
        content,
        (
            "attack",
            "cryptanalysis",
            "security analysis",
            "parameter",
            "parameters",
            "estimator",
            "implementation",
            "side-channel",
            "fault",
            "bootstrapping optimization",
            "noise analysis",
        ),
    )
    has_application_language = _matches_text(
        content,
        (
            "analytics",
            "machine learning",
            "gradient boosting",
            "healthcare",
            "finance",
            "inference",
            "database",
            "pir",
            "private information retrieval",
        ),
    )
    return has_application_language and not has_direct_security_or_parameter


def _is_weak_implementation_audit(record: PaperRecord) -> bool:
    text = _content_text(record)
    if not _matches_text(text, ("implementation", "implementations", "audit", "production", "constant-time")):
        return False
    if _has_specific_scheme(record) and _has_implementation_risk(record):
        return False
    return _matches_text(text, ("implementation", "implementations", "audit", "production"))


def _only_generic_lattice_or_lwe(record: PaperRecord, hit_names: set[str]) -> bool:
    if hit_names:
        return False
    text = _combined_text(record)
    has_generic_term = _matches_text(text, ("lattice", "lwe", "learning with errors"))
    has_specific_context = _matches_text(
        text,
        (
            "attack",
            "cryptanalysis",
            "bkz",
            "lll",
            "module-sis",
            "mlwe",
            "kyber",
            "ml-kem",
            "dilithium",
            "ml-dsa",
            "falcon",
            "fhe",
            "commitment",
        ),
    )
    return has_generic_term and not has_specific_context


def priority_label_for_score(score: int) -> str:
    for threshold, label in PRIORITY_LABELS:
        if score >= threshold:
            return label
    return "低相关"


def priority_label(record: PaperRecord) -> str:
    if has_calibrated_recommendation(record):
        return {
            "Strong": "必须精读",
            "Medium": "建议精读",
            "Low": "可略读",
            "Backfill": "暂存",
            TODO_VERIFY: "低相关",
        }.get(record.recommendation_level, priority_label_for_score(reading_priority_score(record)))
    return priority_label_for_score(reading_priority_score(record))


def reason_for_priority(record: PaperRecord) -> str:
    score = reading_priority_score(record)
    label = priority_label_for_score(score)
    if has_calibrated_recommendation(record):
        action = _action_text(record)
        tags = "、".join(record.user_relevance_tags[:4]) if record.user_relevance_tags else "TODO_VERIFY"
        risks = "；风险：" + "、".join(record.recommendation_risk_flags[:4]) if record.recommendation_risk_flags else ""
        return f"{priority_label(record)}：命中用户研究轴：{tags}。分数 {score}/100；下一步动作：{action}{risks}。"
    hits = _priority_hits(record)
    action = ACTION_LABELS[ACTION_BY_PRIORITY_LABEL[label]]
    if not hits:
        if record.relevance_label == "D":
            return f"{label}：未命中你的格密码主线关键词，且分类为 D，分数 {score}/100 合理；下一步动作：{action}。"
        return (
            f"{label}：虽然通过基础相关性筛选，但暂未命中 AI4Lattice、LWE/MLWE 攻击、BKZ、"
            f"Module-SIS 或标准格方案等精读主线，分数 {score}/100；下一步动作：{action}。"
        )
    hit_names = [name for name, _, _ in sorted(hits, key=lambda hit: PRIORITY_TIE_RANK.get(hit[0], 99))]
    mainline = "、".join(hit_names[:3])
    cap_note = _priority_cap_note(record, set(hit_names))
    if label == "必须精读":
        judgment = "直接贴近你的核心研究主线，适合今天进入精读或组会候选。"
    elif label == "建议精读":
        judgment = "强相关但可能偏实现、理论背景或间接支撑，适合本周系统阅读。"
    elif label == "可略读":
        judgment = "与主线有关但不够直接，适合作为 related work 或背景素材。"
    elif label == "暂存":
        judgment = "相关性较弱或证据不足，先保留标题和链接即可。"
    else:
        judgment = "与当前主线距离较远，不建议投入阅读时间。"
    return f"{label}：命中主线：{mainline}。分数 {score}/100 的原因是{judgment}{cap_note}下一步动作：{action}。"


def _priority_cap_note(record: PaperRecord, hit_names: set[str]) -> str:
    notes: list[str] = []
    if _is_fhe_application(record, hit_names):
        notes.append("它更像 FHE 应用论文，未直接服务 LWE/MLWE 攻击或参数估计，因此已做上限控制。")
    if "broader PQC implementation and standardization" in hit_names and not (
        _has_specific_scheme(record) or hit_names & {"LWE/RLWE/MLWE attacks", "BKZ/LLL/G6K/fplll/sieving"}
    ):
        notes.append("它偏泛 PQC/标准化背景，不按核心格攻击论文处理。")
    if _is_weak_implementation_audit(record):
        notes.append("它虽涉及 implementation/audit，但未明确呈现 ML-KEM/ML-DSA/Kyber/Dilithium/Falcon 安全后果。")
    if not record.abstract.strip():
        notes.append("摘要缺失，不能轻易上调到最高精读区间。")
    return (" " + " ".join(notes) + " ") if notes else " "


def _sort_by_reading_priority(records: list[PaperRecord]) -> list[PaperRecord]:
    return sorted(
        records,
        key=lambda record: (
            -reading_priority_score(record),
            _priority_tie_rank(record),
            -record.relevance_score,
            record.title.lower(),
        ),
    )


def _priority_tie_rank(record: PaperRecord) -> int:
    hits = _priority_hits(record)
    if not hits:
        return 99
    return min(PRIORITY_TIE_RANK.get(name, 99) for name, _, _ in hits)


def why_it_matters(record: PaperRecord) -> str:
    tags = set(research_tags(record))
    reasons: list[str] = []
    if tags & {"MLWE", "LWE", "RLWE", "ML-KEM"}:
        reasons.append("它直接服务 LWE/MLWE 与 ML-KEM 安全主线，可用于参数估计、攻击面梳理或方案比较。")
    if tags & {"SIS", "Module-SIS", "ML-DSA", "Commitments", "Falcon"}:
        reasons.append("它可能支撑 Module-SIS 原语、承诺、签名或短平快小论文选题。")
    if tags & {"Lattice Reduction", "Cryptanalysis"}:
        reasons.append("它可作为 BKZ、primal/dual/hybrid attack 的 baseline、标签或代价模型来源。")
    if "AI4Lattice" in tags:
        reasons.append("它与 AI-assisted lattice cryptanalysis 相关，但需要区分 toy regime 与真实攻击子程序价值。")
    if "PQC Implementation" in tags:
        reasons.append("它可能服务 ML-KEM/ML-DSA 实现、安全工程、侧信道/故障或可复现实验叙事。")
    if "FHE" in tags:
        reasons.append("它扩展了格密码主线中的 FHE、CKKS/BFV/BGV/TFHE 或 bootstrapping 背景。")
    if reasons:
        return "".join(reasons)
    return record.reason or "目前更适合作为格密码/PQC 研究叙事中的背景线索，需读摘要确认真实关联。"


def research_hooks_for_record(record: PaperRecord) -> list[str]:
    tags = set(research_tags(record))
    hooks: list[str] = []
    if tags & {"Module-SIS", "SIS", "Commitments", "ML-DSA"}:
        hooks.append("检查能否改写成 Module-SIS commitment/chameleon hash 小原语，并给出更干净的参数化。")
    if tags & {"LWE", "MLWE", "ML-KEM"}:
        hooks.append("抽取参数、攻击假设和安全 margin，整理成可复现的 MLWE/ML-KEM estimation notebook。")
    if tags & {"Lattice Reduction", "Cryptanalysis"}:
        hooks.append("把其中的攻击代价模型作为 Swin-guided coordinate selection 或 hybrid ranking 的 baseline。")
    if "AI4Lattice" in tags:
        hooks.append("一周内复现实验 toy benchmark，验证学习信号能否接入 BKZ/primal/dual 的经典攻击接口。")
    if not hooks:
        hooks.append("保留为 related work 素材，用于加强 PQC/lattice motivation 段落。")
    return hooks[:3]


def advisor_questions_for_record(record: PaperRecord) -> list[str]:
    tags = set(research_tags(record))
    questions: list[str] = []
    if tags & {"Module-SIS", "SIS", "Commitments"}:
        questions.append("这篇工作的假设或结构能否转成 Module-SIS commitment / chameleon hash 方向，并形成足够的新意？")
    if tags & {"LWE", "MLWE", "ML-KEM"}:
        questions.append("它的 LWE/MLWE 参数区间是否足够接近 ML-KEM，值得纳入我的主线吗？")
    if tags & {"Lattice Reduction", "Cryptanalysis"}:
        questions.append("其中的 scoring 或 cost model 能否接入 primal、dual 或 hybrid attack 做可复现实验？")
    if "AI4Lattice" in tags:
        questions.append("这个 ML 结果只是 toy-regime phenomenon，还是能抽象成有价值的格密码分析子程序？")
    if not questions:
        questions.append("这篇是否只适合 related work，还是能支撑 PhD 申请研究主线中的一个清晰分支？")
    return questions[:3]


def record_intelligence(record: PaperRecord) -> dict[str, object]:
    tags = record.user_relevance_tags if has_calibrated_recommendation(record) and record.user_relevance_tags else research_tags(record)
    score = reading_priority_score(record)
    return {
        "tags": tags,
        "research_tags": tags,
        "priority": record.reading_priority,
        "reading_priority_score": score,
        "priority_label": priority_label_for_score(score),
        "reason_for_priority": reason_for_priority(record),
        "why_it_matters": why_it_matters(record),
        "suggested_action": suggested_action(record),
        "research_hooks": research_hooks_for_record(record),
        "advisor_questions": advisor_questions_for_record(record),
        "source_health_ref": record.source.split(",")[0].strip(),
    }


def _source_status(item: dict[str, object]) -> str:
    status = str(item.get("health_status") or item.get("status") or "").lower()
    if status in {"green", "yellow", "red"}:
        return status
    errors = item.get("errors") if isinstance(item.get("errors"), list) else []
    warnings = item.get("warnings") if isinstance(item.get("warnings"), list) else []
    if errors:
        return "red"
    if warnings:
        return "yellow"
    if item.get("final_records") or item.get("date_filtered_candidates"):
        return "green"
    return "yellow"


def _source_status_text(item: dict[str, object]) -> str:
    status = _source_status(item)
    if status == "green":
        return "绿色：正常"
    if status == "yellow":
        return "黄色：降级"
    return "红色：失败"


def _source_health_brief(source_health: list[dict[str, object]] | None) -> str:
    if not source_health:
        return "暂无 source health 数据"
    green = [str(item.get("source")) for item in source_health if _source_status(item) == "green"]
    yellow = [str(item.get("source")) for item in source_health if _source_status(item) == "yellow"]
    red = [str(item.get("source")) for item in source_health if _source_status(item) == "red"]
    parts = []
    if green:
        parts.append("绿色正常：" + "、".join(green[:4]))
    if yellow:
        parts.append("黄色降级：" + "、".join(yellow[:4]))
    if red:
        parts.append("红色失败：" + "、".join(red[:4]))
    return "；".join(parts) if parts else "暂无 source health 数据"


def _source_health_counts(source_health: list[dict[str, object]] | None) -> dict[str, int]:
    counts = {"green": 0, "yellow": 0, "red": 0}
    for item in source_health or []:
        status = _source_status(item)
        if status in counts:
            counts[status] += 1
    return counts


def _degraded_source_names(source_health: list[dict[str, object]] | None) -> list[str]:
    names: list[str] = []
    for item in source_health or []:
        if _source_status(item) in {"yellow", "red"}:
            names.append(str(item.get("source", "unknown")))
    return names


def _daily_reading_verdict(
    primary_records: list[PaperRecord],
    routed_records: list[PaperRecord],
    source_health: list[dict[str, object]] | None,
) -> str:
    strong = [record for record in primary_records if record.recommendation_level == "Strong"]
    medium = [record for record in primary_records if record.recommendation_level == "Medium"]
    verify_first = [record for record in [*primary_records, *routed_records] if record.recommendation_level == TODO_VERIFY]
    high_value_backfill = [
        record
        for record in routed_records
        if record.research_value_score >= 70 or record.recommendation_level == "Backfill"
    ]
    degraded = _degraded_source_names(source_health)

    if strong:
        action = f"今日优先读 {len(strong)} 篇 Strong primary-new。"
    elif medium:
        action = f"今日可读 {len(medium)} 篇 Medium primary-new，先略读再决定是否精读。"
    elif high_value_backfill:
        action = f"今日无 primary-new 必读；有 {len(high_value_backfill)} 篇 backfill/older 项目可作为背景或本周阅读。"
    elif verify_first:
        action = f"今日无可直接阅读的新论文；有 {len(verify_first)} 条 TODO_VERIFY 线索，先核验来源/日期/摘要。"
    else:
        action = "今日无值得投入阅读时间的 primary-new 论文；可跳过或扩大窗口做周视角检查。"

    if degraded:
        action += f" Source health 有降级源：{'、'.join(degraded[:5])}，结论需保守。"
    return action


def _reading_action_counts(records: list[PaperRecord], routed_records: list[PaperRecord]) -> dict[str, int]:
    all_items = [*records, *routed_records]
    counts = {"read_now": 0, "skim": 0, "save_or_backfill": 0, "verify_first": 0}
    for record in all_items:
        action = suggested_action(record)
        if record.recommendation_level == TODO_VERIFY or "TODO_VERIFY" in action:
            counts["verify_first"] += 1
        elif record.primary_today_new_eligible and action == "Read today":
            counts["read_now"] += 1
        elif action in {"Read this week", "Skim for related work"}:
            counts["skim"] += 1
        else:
            counts["save_or_backfill"] += 1
    return counts


def _source_health_risk_line(source_health: list[dict[str, object]] | None) -> str:
    counts = _source_health_counts(source_health)
    degraded = _degraded_source_names(source_health)
    if not source_health:
        return "Source health：暂无 ledger；如日报为空或低信号，需避免过度解读。"
    base = f"Source health：green={counts['green']}，yellow={counts['yellow']}，red={counts['red']}"
    if degraded:
        return base + f"；降级源：{'、'.join(degraded[:6])}；建议阅读前核验关键来源。"
    return base + "；未见降级源。"


def _metadata_text(metadata: dict[str, object] | None, key: str, default: str = "unknown") -> str:
    if not metadata:
        return default
    value = metadata.get(key)
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _supersedes_text(metadata: dict[str, object] | None) -> str:
    if not metadata:
        return "无"
    supersedes = metadata.get("supersedes")
    if not isinstance(supersedes, dict) or not supersedes:
        return "无"
    collector = supersedes.get("collector") or "unknown"
    run_date = supersedes.get("run_date") or "unknown"
    quality = supersedes.get("quality_status") or "unknown"
    return f"{collector} / {run_date} / {quality}"


def _paper_header(record: PaperRecord, index: int | None = None) -> str:
    prefix = f"{index}. " if index is not None else ""
    return f"### {prefix}{record.title}"


def _display_value(value: object, default: str = "unknown") -> str:
    if value is None or value == "" or value == []:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "、".join(str(item) for item in value) if value else default
    return str(value)


def _short_list(values: list[str], limit: int = 4, default: str = "none") -> str:
    selected = [str(value) for value in values if str(value).strip()]
    if not selected:
        return default
    rendered = "、".join(selected[:limit])
    if len(selected) > limit:
        rendered += f"、等 {len(selected)} 项"
    return rendered


def _truncate_text(text: str, limit: int = 280) -> str:
    compact = " ".join(str(text or "").split())
    if not compact:
        return "TODO_VERIFY"
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."


def _placement_label(record: PaperRecord) -> str:
    if record.primary_today_new_eligible and record.freshness_bucket == "primary_today_new":
        return "primary today/new"
    if record.freshness_bucket == "date_uncertain_todo_verify" or record.recommendation_level == TODO_VERIFY:
        return "TODO_VERIFY / non-primary"
    if record.freshness_bucket in {"backfill", "important_older_item"}:
        return "backfill / older non-primary"
    return f"{record.freshness_bucket} / non-primary"


def _risk_flags(record: PaperRecord) -> list[str]:
    flags = list(record.recommendation_risk_flags or [])
    flags.extend(flag for flag in (record.TODO_VERIFY_flags or []) if flag not in flags)
    if record.source_health and record.source_health.lower() in {"yellow", "red"}:
        flags.append(f"source_health_{record.source_health.lower()}")
    if not record.source_health:
        flags.append("source_health_missing")
    if record.venue_status == TODO_VERIFY and "venue_todo_verify" not in flags:
        flags.append("venue_todo_verify")
    if record.CCF_rank in {"unknown", TODO_VERIFY} and "ccf_uncertain" not in flags:
        flags.append("ccf_uncertain")
    return sorted(dict.fromkeys(str(flag) for flag in flags if str(flag).strip()))


def _generated_marker_summary(record: PaperRecord) -> str:
    markers: list[str] = []
    for field_name in ("abstract_zh", "conclusion_zh"):
        value = str(getattr(record, field_name) or "")
        if value.startswith("model-generated"):
            markers.append(f"{field_name}=model-generated/translated")
        elif value.startswith(TODO_VERIFY):
            markers.append(f"{field_name}=TODO_VERIFY")
    return "；".join(markers) if markers else "none"


def _recommendation_display_lines(record: PaperRecord) -> list[str]:
    reason = record.recommendation_reason or reason_for_priority(record)
    score_bits = [f"recommendation_score {record.recommendation_score}"]
    if record.research_value_score:
        score_bits.append(f"research_value_score {record.research_value_score}")
    score_bits.append(f"relevance {record.relevance_label}/{record.relevance_score}")
    return [
        "#### Recommendation / Action",
        f"- Recommendation：{record.recommendation_level}（{'; '.join(score_bits)}）",
        f"- Suggested action：{_action_text(record)}",
        f"- Why it matters：{_truncate_text(reason, 220)}",
        "- Score note：recommendation_score 是 freshness/risk-gated 行动分；research_value_score 是内在研究价值，不能覆盖 freshness gate。",
    ]


def _workflow_display_lines(record: PaperRecord) -> list[str]:
    intel = record_intelligence(record)
    tags = record.user_relevance_tags if record.user_relevance_tags else list(intel["tags"])
    hooks = intel["research_hooks"] if isinstance(intel["research_hooks"], list) else []
    questions = intel["advisor_questions"] if isinstance(intel["advisor_questions"], list) else []
    return [
        "#### User Workflow",
        f"- User relevance：{_short_list([str(tag) for tag in tags], default='TODO_VERIFY')}",
        f"- PhD / application：{record.phd_application_relevance or 'TODO_VERIFY'}",
        f"- Blog / Obsidian / project hook：{_truncate_text('；'.join(str(item) for item in hooks[:2]) if hooks else '暂无', 220)}",
        f"- PI / advisor question：{_truncate_text('；'.join(str(item) for item in questions[:2]) if questions else '暂无', 220)}",
    ]


def _risk_display_lines(record: PaperRecord) -> list[str]:
    risks = _risk_flags(record)
    risk_summary = _short_list(risks, limit=6, default="none")
    return [
        "#### Risk / TODO_VERIFY",
        f"- Risk strip：{risk_summary}",
        f"- TODO_VERIFY visible：{'yes' if risks or record.recommendation_level == TODO_VERIFY else 'no'}",
        f"- Venue / CCF：{record.venue or 'unknown'}；venue_type={record.venue_type}；CCF={record.CCF_rank}；venue_status={record.venue_status}",
        f"- Source health：{record.source_health or 'unknown'}",
        f"- Generated/translated markers：{_generated_marker_summary(record)}",
    ]


def _summary_display_lines(record: PaperRecord) -> list[str]:
    return [
        "#### Abstract / Conclusion",
        f"- abstract_en：{_truncate_text(record.abstract_en or record.abstract or TODO_VERIFY, 260)}",
        f"- abstract_zh：{_truncate_text(record.abstract_zh or TODO_VERIFY, 260)}",
        f"- conclusion_en：{_truncate_text(record.conclusion_en or TODO_VERIFY, 260)}",
        f"- conclusion_zh：{_truncate_text(record.conclusion_zh or TODO_VERIFY, 260)}",
    ]


def _audit_detail_lines(record: PaperRecord) -> list[str]:
    intel = record_intelligence(record)
    rationale = build_recommendation_rationale(record)
    link = f"[来源链接]({record.source_url})" if record.source_url else "unknown"
    hooks = intel["research_hooks"] if isinstance(intel["research_hooks"], list) else []
    questions = intel["advisor_questions"] if isinstance(intel["advisor_questions"], list) else []
    todo_verify = "；".join(rationale.todo_verify) if rationale.todo_verify else "TODO_VERIFY：阅读正文核验证明、参数、实验与限制条件。"
    return [
        "#### Audit Details",
        f"- 作者：{', '.join(record.authors) if record.authors else 'unknown'}",
        f"- 日期/年份：{record.publication_date or record.update_date or 'unknown'}",
        f"- publication_date：{record.publication_date or 'unknown'}",
        f"- announcement_date：{record.announcement_date or 'unknown'}",
        f"- update_date：{record.update_date or 'unknown'}",
        f"- first_seen_date：{record.first_seen_date or 'unknown'}",
        f"- selected_date_basis：{record.selected_date_basis}",
        f"- freshness_bucket：{record.freshness_bucket}",
        f"- freshness_reason：{record.freshness_reason or 'unknown'}",
        f"- primary_today_new_eligible：{record.primary_today_new_eligible}",
        f"- 来源：{record.source}",
        f"- venue：{record.venue or 'unknown'}",
        f"- venue_type：{record.venue_type}",
        f"- publisher_or_source：{record.publisher_or_source}",
        f"- CCF_rank：{record.CCF_rank}",
        f"- venue_status：{record.venue_status}",
        f"- venue_scope：expanded_security_crypto_systems={record.venue_expanded_security_crypto_systems_scope}；relevance={record.venue_relevance}；confidence={record.venue_confidence}",
        f"- 链接：{link}",
        f"- 论文事实：以上为 source metadata；如作者、日期或 venue 缺失，进入精读前需手动核验。",
        f"- 分类/分数：{record.relevance_label} / {record.relevance_score}",
        f"- recommendation_level：{record.recommendation_level}",
        f"- recommendation_score：{record.recommendation_score}",
        f"- recommendation_reason：{record.recommendation_reason or 'TODO_VERIFY'}",
        f"- user_relevance_tags：{', '.join(record.user_relevance_tags) if record.user_relevance_tags else 'TODO_VERIFY'}",
        f"- phd_application_relevance：{record.phd_application_relevance or 'TODO_VERIFY'}",
        f"- recommendation_risk_flags：{', '.join(record.recommendation_risk_flags) if record.recommendation_risk_flags else 'none'}",
        f"- recommendation_evidence_basis：{', '.join(record.recommendation_evidence_basis) if record.recommendation_evidence_basis else 'TODO_VERIFY'}",
        f"- research_value_score：{record.research_value_score}",
        f"- primary_action_allowed：{record.primary_action_allowed}",
        f"- recommendation_score_breakdown：{record.recommendation_score_breakdown if record.recommendation_score_breakdown else 'TODO_VERIFY'}",
        f"- title_en：{record.title_en or record.title}",
        f"- title_zh：{record.title_zh or record.chinese_title or 'TODO_VERIFY'}",
        f"- abstract_en：{record.abstract_en or 'TODO_VERIFY'}",
        f"- abstract_zh：{record.abstract_zh or 'TODO_VERIFY'}",
        f"- conclusion_en：{record.conclusion_en or 'TODO_VERIFY'}",
        f"- conclusion_zh：{record.conclusion_zh or 'TODO_VERIFY'}",
        f"- lattice_crypto_relevance：{record.lattice_crypto_relevance or 'TODO_VERIFY'}",
        f"- TODO_VERIFY_flags：{', '.join(record.TODO_VERIFY_flags) if record.TODO_VERIFY_flags else 'none'}",
        f"- source_urls：{', '.join(record.source_urls) if record.source_urls else (record.source_url or 'unknown')}",
        f"- source_refs：{', '.join(record.source_refs) if record.source_refs else (record.source_url or 'unknown')}",
        f"- evidence_tier：{record.evidence_tier or 'unknown'}",
        f"- source_health：{record.source_health or 'unknown'}",
        f"- {concise_ranking_explanation(record)}",
        f"- {anchor_evidence_text(record)}",
        f"- false-positive risk note：{false_positive_risk_text(record)}",
        f"- priority：{intel['priority']}",
        f"- reading_priority_score：{intel['reading_priority_score']}",
        f"- priority_label：{intel['priority_label']}",
        f"- reason_for_priority：{intel['reason_for_priority']}",
        f"- research_tags：{', '.join(intel['tags']) if intel['tags'] else 'unknown'}",
        f"- why_it_matters：{intel['why_it_matters']}",
        "- Recommendation rationale:",
        f"  - Paper problem: {rationale.problem_summary}",
        f"  - Method / construction / attack / implementation: {rationale.method_summary}",
        f"  - Main contribution: {rationale.contribution_summary}",
        f"  - Radar relevance: {rationale.radar_relevance}",
        f"  - Why read / skim / track / ignore: {rationale.recommendation_reason}",
        f"  - Evidence basis: {', '.join(rationale.evidence_basis)}；confidence={rationale.confidence}",
        f"  - TODO_VERIFY: {todo_verify}",
        f"- suggested_action：{_action_text(record)}",
        f"- Semantic Scholar advisory metadata：{semantic_scholar_advisory_text(record)}",
        f"- research_hooks：{'；'.join(str(item) for item in hooks) if hooks else '暂无'}",
        f"- advisor_questions：{'；'.join(str(item) for item in questions) if questions else '暂无'}",
    ]


def _basic_paper_lines(record: PaperRecord) -> list[str]:
    lines = [
        f"- Placement：{_placement_label(record)}",
        f"- Source / date basis：{record.source}；selected_date_basis={record.selected_date_basis}；freshness_bucket={record.freshness_bucket}",
        f"- Venue / CCF：{record.venue or 'unknown'}；{record.venue_type}；CCF={record.CCF_rank}",
    ]
    lines.extend(_recommendation_display_lines(record))
    lines.extend(_workflow_display_lines(record))
    lines.extend(_risk_display_lines(record))
    lines.extend(_summary_display_lines(record))
    lines.extend(_audit_detail_lines(record))
    return lines


def _append_records(lines: list[str], records: list[PaperRecord], empty_text: str, limit: int | None = None) -> None:
    selected = records[:limit] if limit else records
    if not selected:
        lines.extend([empty_text, ""])
        return
    for index, record in enumerate(selected, start=1):
        lines.append(_paper_header(record, index))
        lines.extend(_basic_paper_lines(record))
        lines.append("")


def _append_freshness_routed_section(lines: list[str], records: list[PaperRecord]) -> None:
    lines.extend(["## 2b. 回填 / 较早 / 待核验项目", ""])
    if not records:
        lines.extend(["今日没有被 freshness gate 移出 primary today/new 的项目。", ""])
        return
    lines.append("以下项目未进入 primary today/new；它们只能作为 backfill、older item、official update 或 TODO_VERIFY 跟踪。")
    lines.append("")
    grouped: dict[str, list[PaperRecord]] = {}
    for record in records:
        grouped.setdefault(record.freshness_bucket, []).append(record)
    for bucket in sorted(grouped):
        lines.extend([f"### {bucket}", ""])
        for index, record in enumerate(_sort_by_reading_priority(grouped[bucket]), start=1):
            lines.append(_paper_header(record, index))
            lines.extend(_basic_paper_lines(record))
            lines.append("")


def _record_identifier(record: PaperRecord) -> str:
    return (
        record.source_url
        or record.paper_id
        or record.arxiv_id
        or record.eprint_id
        or record.doi
        or "unknown"
    )


def _research_section_entry(record: PaperRecord, section: str) -> str:
    reason = ""
    if section in {IDEA_BANK_CANDIDATES, PAPER_PLAN_CANDIDATES}:
        reason = f"；候选原因：{candidate_reason(record, section)}"
    return (
        f"- {record.title}｜{record.relevance_label} / {record.relevance_score}｜"
        f"{record.source}｜{_record_identifier(record)}｜{concise_ranking_explanation(record)}{reason}"
    )


def _append_research_sections(lines: list[str], records: list[PaperRecord]) -> None:
    lines.extend(["### Research-Oriented Sections", ""])
    mapping = sectioned_records(records)
    for section in PAPER_SECTION_ORDER:
        lines.extend([f"#### {section}", ""])
        section_records = mapping.get(section, [])
        if not section_records:
            lines.extend(["- No matching records.", ""])
            continue
        for record in _sort_by_reading_priority(section_records):
            lines.append(_research_section_entry(record, section))
        lines.append("")


def _section_records(records: list[PaperRecord], section: str) -> list[PaperRecord]:
    return [record for record in records if _matches(record, SECTION_TERMS[section])]


def _dedup_records(records: list[PaperRecord]) -> list[PaperRecord]:
    seen: set[str] = set()
    unique: list[PaperRecord] = []
    for record in records:
        key = record.paper_id or record.source_url or record.title.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def _append_ai_section(lines: list[str], records: list[PaperRecord]) -> None:
    lines.extend(["## 3. AI4Lattice 与机器学习辅助密码分析", ""])
    selected = _section_records(records, "ai4lattice")
    if not selected:
        lines.extend(["今日没有 AI4Lattice 或 neural cryptanalysis 方向的入选论文。", ""])
        return
    for index, record in enumerate(selected, start=1):
        text = _combined_text(record)
        model_role = "coordinate selection / ranking" if "coordinate" in text or "ranking" in text else "distinguisher / subroutine candidate"
        lines.append(_paper_header(record, index))
        lines.extend(_basic_paper_lines(record))
        lines.append(f"- 模型角色：{model_role}")
        lines.append("- 真实性判断：默认按 toy-only/benchmark-only 保守处理，需核对维度、分布、泄漏假设和经典攻击接口。")
        lines.append("- 经典攻击接口：重点检查 BKZ / primal / dual / hybrid / BDD / estimator 是否可接入。")
        lines.append("- 一周可做实验：复现最小 benchmark，并和简单 estimator 或 BKZ-derived baseline 对比。")
        lines.append("- 潜在论文 idea：把 ML 当 ranking、pruning、parameter prediction 子程序，而不是宣称端到端恢复真实 LWE secret。")
        lines.append("")


def _append_reduction_section(lines: list[str], records: list[PaperRecord]) -> None:
    lines.extend(["## 4. 格基约简与经典攻击", ""])
    selected = _section_records(records, "reduction")
    if not selected:
        lines.extend(["今日没有 lattice reduction / BKZ / SVP-CVP / primal-dual-hybrid attack 方向的入选论文。", ""])
        return
    for index, record in enumerate(selected, start=1):
        lines.append(_paper_header(record, index))
        lines.extend(_basic_paper_lines(record))
        lines.append("- 攻击相关性：优先看是否影响 BKZ、primal、dual、hybrid、BDD、estimator 或 secret recovery workflow。")
        lines.append("- AI4Lattice 接口：若参数、label、score 或 cost model 可复现，可作为 Swin-guided coordinate selection baseline。")
        lines.append("- 阅读策略：有代码/参数/estimator 脚本则适合实验复现，否则先作为理论背景阅读。")
        lines.append("")


def _append_pqc_section(lines: list[str], records: list[PaperRecord]) -> None:
    lines.extend(["## 5. PQC 标准、原语与实现", ""])
    selected = _dedup_records(
        [
            *(_section_records(records, "lwe_mlwe")),
            *(_section_records(records, "sis_signatures")),
            *(_section_records(records, "fhe_pqc")),
        ]
    )
    if not selected:
        lines.extend(["今日没有 LWE/MLWE/Module-SIS/ML-KEM/ML-DSA/FHE/PQC implementation 方向的入选论文。", ""])
        return
    for index, record in enumerate(selected, start=1):
        lines.append(_paper_header(record, index))
        lines.extend(_basic_paper_lines(record))
        lines.append("- 与主线关系：检查是否服务 MLWE/Module-SIS 小原语、ML-KEM/ML-DSA 安全实现、FHE 或 PQC 部署叙事。")
        lines.append("- 风险判断：若只是泛 PQC 或泛系统论文，保守放入背景引用，不作为今日必读。")
        lines.append("")


def _append_reading_queue(lines: list[str], records: list[PaperRecord]) -> None:
    lines.extend(["## 6. 阅读队列与精读建议", ""])
    sorted_records = _sort_by_reading_priority(records)
    buckets = {
        "必须精读": [record for record in sorted_records if priority_label(record) == "必须精读"][:5],
        "建议精读": [record for record in sorted_records if priority_label(record) == "建议精读"][:5],
        "可略读": [record for record in sorted_records if priority_label(record) == "可略读"][:8],
        "暂存": [record for record in sorted_records if priority_label(record) == "暂存"][:8],
    }
    for title, bucket in buckets.items():
        lines.extend([f"### {title}", ""])
        if not bucket:
            lines.extend(["- 无。", ""])
            continue
        for record in bucket:
            lines.append(
                f"- {record.title}（{record.source}，reading_priority_score {reading_priority_score(record)}，"
                f"relevance {record.relevance_score}）：{reason_for_priority(record)}"
            )
        lines.append("")


def _append_idea_and_questions(lines: list[str], records: list[PaperRecord]) -> None:
    lines.extend(["## 7. 可孵化研究 idea 与导师讨论问题", ""])
    if not records:
        lines.append("今日没有可直接孵化的论文线索；建议扩大窗口到 7d 或 30d 后再做周计划。")
        lines.append("")
    for index, record in enumerate(records[:5], start=1):
        tags = set(research_tags(record))
        if "AI4Lattice" in tags:
            title = "Swin-guided ranking 作为格攻击子程序"
            experiment = "构造小型 coordinate/candidate ranking benchmark，并与经典启发式对比。"
            contribution = "一个可复现的 ML-assisted subroutine，而不是端到端破解真实 LWE。"
        elif tags & {"Module-SIS", "SIS", "Commitments"}:
            title = "Module-SIS 小原语或承诺变体"
            experiment = "实例化参数，写出最小 correctness/security sketch，并检查 novelty。"
            contribution = "适合导师讨论或短论文定位的紧凑原语方向。"
        elif tags & {"Lattice Reduction", "Cryptanalysis"}:
            title = "可复现格攻击估计 baseline"
            experiment = "复现论文 cost model，并与 lattice-estimator 或 BKZ baseline 比较。"
            contribution = "为后续 MLWE/Module-SIS/AI4Lattice 工作提供透明参数估计 artifact。"
        else:
            title = "格密码/PQC related-work bridge"
            experiment = "整理假设、参数、结论和与你 PhD 主线的关系。"
            contribution = "加强申请材料和论文 related work 的叙事密度。"
        lines.extend(
            [
                f"### idea {index}: {title}",
                f"- 来源论文：{record.title}",
                f"- 为什么可行：{why_it_matters(record)}",
                f"- 最小可行实验：{experiment}",
                f"- 预期贡献：{contribution}",
                "- 主要风险：metadata 可能高估相关性；投入前必须确认假设、维度、参数和可复现性。",
                "- 适合定位：workshop、短论文、组会实验或导师内部选题评估。",
                "",
            ]
        )

    questions: list[str] = []
    for record in records:
        questions.extend(advisor_questions_for_record(record))
    if not questions:
        questions = [
            "下次组会前是否应该扩大窗口到 7d 或 30d？",
            "当 arXiv/OpenAlex/Semantic Scholar 降级时，是否应优先依赖 IACR ePrint？",
            "当前主线更适合押 Module-SIS 小原语，还是 AI-assisted lattice cryptanalysis 子程序？",
        ]
    lines.extend(["### 导师讨论问题", ""])
    for index, question in enumerate(list(dict.fromkeys(questions))[:8], start=1):
        lines.append(f"{index}. {question}")
    lines.append("")


def _append_source_health_and_empty(
    lines: list[str],
    records: list[PaperRecord],
    filtered_count: int,
    source_health: list[dict[str, object]] | None,
    warnings: list[str] | None,
    metadata: dict[str, object] | None = None,
) -> None:
    lines.extend(["## 8. 数据源健康与空报告处理", ""])
    ledger_date = _metadata_text(metadata, "target_date", "")
    if ledger_date:
        lines.append(
            f"- Source Health Ledger：`audits/source-health/{ledger_date}.json`；"
            f"`audits/source-health/{ledger_date}.md`"
        )
    lines.extend([f"### {SOURCE_HEALTH_SUMMARY}", ""])
    if metadata:
        if metadata.get("collector") == "github_actions" or metadata.get("quality_status") == "provisional":
            lines.append(
                "- 采集质量提示：该报告由 GitHub Actions 生成，可能受限于 GitHub runner 网络环境；"
                "建议后续由本地 Codex backfill 增强。"
            )
        elif metadata.get("quality_status") == "authoritative_backfill":
            lines.append("- 采集质量提示：该报告为本地 Codex 权威回填版本，可替代此前的 provisional 日报。")
    lines.append(f"- D 类/过滤数量：{filtered_count}")
    lines.append(f"- Warning 数量：{len(warnings or [])}")
    lines.append(f"- Source health 摘要：{_source_health_brief(source_health)}")
    lines.append(f"- Source health caveat：{source_health_caveat_text(source_health)}")
    lines.append("")
    if source_health:
        lines.append("| Source | Raw | Norm | Date | Dedup | Rel | Threshold | Final | 状态 | Error Type | Retryable |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |")
        for item in source_health:
            lines.append(
                "| {source} | {raw} | {normalized} | {date_filtered} | {deduped} | {relevance} | {threshold} | {final} | {status} | {error_type} | {retryable} |".format(
                    source=item.get("source", "unknown"),
                    raw=item.get("raw_count", item.get("raw_candidates", 0)),
                    normalized=item.get("normalized_count", item.get("normalized_candidates", 0)),
                    date_filtered=item.get("date_filtered_count", item.get("date_filtered_candidates", 0)),
                    deduped=item.get("deduped_candidates", 0),
                    relevance=item.get("relevance_filtered_candidates", 0),
                    threshold=item.get("scoring_threshold_candidates", 0),
                    final=item.get("final_count", item.get("final_records", 0)),
                    status=_source_status_text(item),
                    error_type=item.get("error_type") or "无",
                    retryable="是" if item.get("retryable") else "否",
                )
            )
        lines.append("")
        for item in source_health:
            source = item.get("source", "unknown")
            source_warnings = item.get("warnings") if isinstance(item.get("warnings"), list) else []
            source_errors = item.get("errors") if isinstance(item.get("errors"), list) else []
            if source_warnings or source_errors:
                detail = "；".join(str(value) for value in [*source_warnings[:2], *source_errors[:2]])
                lines.append(f"- {source} warning/error：{detail}")
            error_message = item.get("error_message")
            if error_message and not (source_warnings or source_errors):
                lines.append(f"- {source} error_message：{error_message}")
            if item.get("query_groups_total"):
                lines.append(
                    f"- {source} query groups：total={item.get('query_groups_total')}，"
                    f"success={item.get('query_groups_success')}，failed={item.get('query_groups_failed')}"
                )
            if item.get("api_key_used") is not None:
                lines.append(f"- {source} API key：{'已配置' if item.get('api_key_used') else '未配置'}")
        lines.append("")
    else:
        lines.extend(["暂无 source health 数据。", ""])

    if records:
        lines.extend(["当前最终入选论文数量非 0，不需要空报告补救。", ""])
        return
    lines.append("今日没有通过筛选的论文。")
    lines.append("如果需要周计划材料，建议扩大窗口重试：")
    lines.append("- `python -m lattice_digest.run --since 7d --output markdown,json --send none`")
    lines.append("- `python -m lattice_digest.run --since 30d --output markdown,json --send none`")
    lines.append("- 最近一次有记录的运行日期：请检查 `data/` 或 `digests/` 中最新日期文件。")
    lines.append("")


def generate_markdown(
    records: list[PaperRecord],
    digest_date: date,
    filtered_count: int = 0,
    source_health: list[dict[str, object]] | None = None,
    warnings: list[str] | None = None,
    since_window: str = "36h",
    metadata: dict[str, object] | None = None,
) -> str:
    all_records = [record for record in records if record.relevance_label in {"A", "B", "C"}]
    records, freshness_routed_records = apply_daily_freshness_policy(all_records, digest_date)
    sorted_records = _sort_by_reading_priority(records)
    high_priority = [record for record in sorted_records if reading_priority_score(record) >= 70]
    topic_counts = Counter(tag for record in all_records for tag in research_tags(record))
    main_topics = [topic for topic, _ in topic_counts.most_common(3)]
    source_names = sorted({record.source for record in all_records})
    action_counts = _reading_action_counts(records, freshness_routed_records)
    has_mainline = any(
        set(research_tags(record)) & {"LWE", "MLWE", "Module-SIS", "Lattice Reduction", "PQC Implementation"}
        for record in all_records
    )
    lines: list[str] = [
        f"# 格密码科研情报日报 - {digest_date.isoformat()}",
        "",
        "## 1. 今日核心结论",
        "",
        "### 今日读什么 / What to read today",
        "",
        f"- Daily verdict：{_daily_reading_verdict(records, freshness_routed_records, source_health)}",
        f"- Action counts：read_now={action_counts['read_now']}；skim={action_counts['skim']}；save/backfill={action_counts['save_or_backfill']}；verify_first={action_counts['verify_first']}",
        f"- Primary/backfill split：primary today/new={len(records)}；backfill/older/TODO_VERIFY={len(freshness_routed_records)}",
        f"- Top-level risk：{_source_health_risk_line(source_health)}",
        "- Reading rule：primary today/new 才能承载今日精读；backfill/TODO_VERIFY 只能作为背景、核验或本周队列。",
        "",
        "### Run metadata / audit snapshot",
        "",
        f"- 最终入选论文数：{len(all_records)}",
        f"- primary today/new 论文数：{len(records)}",
        f"- backfill/older/TODO_VERIFY 论文数：{len(freshness_routed_records)}",
        f"- 高优先级论文数：{len(high_priority)}",
        f"- target_date：{_metadata_text(metadata, 'target_date', digest_date.isoformat())}",
        f"- run_date：{_metadata_text(metadata, 'run_date', digest_date.isoformat())}",
        f"- collector：{_metadata_text(metadata, 'collector', 'local_codex')}",
        f"- quality_status：{_metadata_text(metadata, 'quality_status', 'authoritative')}",
        f"- run_mode：{_metadata_text(metadata, 'run_mode', 'daily')}",
        f"- coverage_start：{_metadata_text(metadata, 'coverage_start')}",
        f"- coverage_end：{_metadata_text(metadata, 'coverage_end')}",
        f"- 检索窗口：{since_window}",
        f"- backfill：{_metadata_text(metadata, 'backfill', 'false')}",
        f"- supersedes：{_supersedes_text(metadata)}",
        f"- 主要来源：{'、'.join(source_names[:5]) if source_names else '无'}",
        f"- 今日主题：{'、'.join(main_topics) if main_topics else '无'}",
        f"- 是否出现 AI4Lattice：{'是' if any('AI4Lattice' in research_tags(record) for record in all_records) else '否'}",
        f"- 是否覆盖 LWE/MLWE/Module-SIS/格基约简/PQC 实现：{'是' if has_mainline else '否'}",
        f"- 数据源健康：{_source_health_brief(source_health)}",
    ]
    if metadata and (metadata.get("collector") == "github_actions" or metadata.get("quality_status") == "provisional"):
        lines.append("- 质量提示：该报告由 GitHub Actions 生成，可能受限于 runner 网络环境；建议后续由本地 Codex backfill 增强。")
    if len(all_records) == 0:
        lines.append("今日未发现值得记录的格密码相关新论文。")
    if warnings:
        lines.append(f"- Warning：{len(warnings)} 条，详见第 8 节。")
    lines.append("")

    lines.extend(["## 2. 高优先级论文", ""])
    _append_records(lines, high_priority, "今日无高优先级论文。", limit=8)
    if not high_priority and freshness_routed_records:
        lines.extend(
            [
                "今日没有 primary-new 高优先级论文；下方回填/TODO_VERIFY 项目不是今日新论文，建议按核验或背景阅读处理。",
                "",
            ]
        )
    elif not high_priority:
        lines.extend(["今日没有 primary-new 高优先级论文；可跳过日报或扩大窗口做周视角检查。", ""])
    _append_freshness_routed_section(lines, freshness_routed_records)

    _append_ai_section(lines, records)
    _append_reduction_section(lines, records)
    _append_pqc_section(lines, records)
    _append_research_sections(lines, records)
    _append_reading_queue(lines, records)
    _append_idea_and_questions(lines, records)
    _append_source_health_and_empty(lines, all_records, filtered_count, source_health, warnings, metadata)
    return "\n".join(lines)
