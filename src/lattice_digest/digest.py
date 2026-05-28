from __future__ import annotations

from collections import Counter
from datetime import date

from lattice_digest.models import PaperRecord


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
    "Read immediately": "立即精读",
    "Add to weekly reading": "加入本周阅读",
    "Use as background citation": "作为背景引用",
    "Monitor only": "仅跟踪",
    "Ignore unless related work needed": "低优先级，除非需要 related work",
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
        45,
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
        42,
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
        36,
        "覆盖 LWE/RLWE/MLWE 或 sparse LWE 攻击，是当前安全分析和实验主线的核心素材。",
    ),
    (
        "primal/dual/hybrid attack",
        ("primal attack", "dual attack", "hybrid attack", "bdd attack", "lattice reduction attack"),
        34,
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
        32,
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
        30,
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
        26,
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
        24,
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
        16,
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
        8,
        "属于 broader PQC 标准化或部署背景，除非明确连接格方案，否则精读优先级较低。",
    ),
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
    tags = set(research_tags(record))
    if record.relevance_score >= 85 or record.relevance_label == "A":
        return "Read immediately"
    if record.relevance_score >= 70 or tags & {"AI4Lattice", "Lattice Reduction", "ML-KEM", "MLWE", "Module-SIS"}:
        return "Add to weekly reading"
    if record.relevance_score >= 55 or tags:
        return "Use as background citation"
    if record.relevance_label == "C":
        return "Monitor only"
    return "Ignore unless related work needed"


def _action_text(record: PaperRecord) -> str:
    action = suggested_action(record)
    return ACTION_LABELS.get(action, action)


def _priority_hits(record: PaperRecord) -> list[tuple[str, int, str]]:
    text = _combined_text(record)
    hits: list[tuple[str, int, str]] = []
    for name, terms, weight, reason in PRIORITY_RULES:
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
            has_attack_context = _matches_text(
                text,
                (
                    "attack",
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
                ),
            )
            if has_lwe_family and has_attack_context:
                hits.append((name, weight, reason))
            continue
        if _matches_text(text, terms):
            hits.append((name, weight, reason))
    return hits


def reading_priority_score(record: PaperRecord) -> int:
    label_base = {"A": 30, "B": 22, "C": 12}.get(record.relevance_label, 0)
    score = label_base + max(0, min(record.relevance_score, 100)) // 5
    hits = _priority_hits(record)
    score += sum(weight for _, weight, _ in hits)

    text = _combined_text(record)
    has_core_hit = any(weight >= 24 for _, weight, _ in hits)
    if "survey" in text and not has_core_hit:
        score -= 10
    if _matches_text(text, ("post-quantum cryptography", "pqc", "standardization")) and not has_core_hit:
        score = min(score, 49)
    if not record.source_url:
        score -= 20
        score = min(score, 49)
    if record.relevance_label == "D":
        score = min(score, 29)
    return max(0, min(100, score))


def priority_label_for_score(score: int) -> str:
    for threshold, label in PRIORITY_LABELS:
        if score >= threshold:
            return label
    return "低相关"


def priority_label(record: PaperRecord) -> str:
    return priority_label_for_score(reading_priority_score(record))


def reason_for_priority(record: PaperRecord) -> str:
    score = reading_priority_score(record)
    label = priority_label_for_score(score)
    hits = _priority_hits(record)
    if not hits:
        if record.relevance_label == "D":
            return f"{label}：未命中你的格密码主线关键词，且分类为 D，默认不投入阅读时间。"
        return f"{label}：虽然通过基础相关性筛选，但暂未命中 AI4Lattice、LWE/MLWE、BKZ、Module-SIS 或标准格方案等精读主线。"
    reasons = [reason for _, _, reason in hits[:3]]
    return f"{label}：阅读优先级 {score}/100。{''.join(reasons)}"


def _sort_by_reading_priority(records: list[PaperRecord]) -> list[PaperRecord]:
    return sorted(
        records,
        key=lambda record: (
            -reading_priority_score(record),
            -record.relevance_score,
            record.title.lower(),
        ),
    )


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
    tags = research_tags(record)
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


def _paper_header(record: PaperRecord, index: int | None = None) -> str:
    prefix = f"{index}. " if index is not None else ""
    return f"### {prefix}{record.title}"


def _basic_paper_lines(record: PaperRecord) -> list[str]:
    intel = record_intelligence(record)
    link = f"[来源链接]({record.source_url})" if record.source_url else "unknown"
    hooks = intel["research_hooks"] if isinstance(intel["research_hooks"], list) else []
    questions = intel["advisor_questions"] if isinstance(intel["advisor_questions"], list) else []
    return [
        f"- 作者：{', '.join(record.authors) if record.authors else 'unknown'}",
        f"- 日期/年份：{record.publication_date or record.update_date or 'unknown'}",
        f"- 来源：{record.source}",
        f"- 链接：{link}",
        f"- 分类/分数：{record.relevance_label} / {record.relevance_score}",
        f"- priority：{intel['priority']}",
        f"- reading_priority_score：{intel['reading_priority_score']}",
        f"- priority_label：{intel['priority_label']}",
        f"- reason_for_priority：{intel['reason_for_priority']}",
        f"- research_tags：{', '.join(intel['tags']) if intel['tags'] else 'unknown'}",
        f"- why_it_matters：{intel['why_it_matters']}",
        f"- suggested_action：{_action_text(record)}",
        f"- research_hooks：{'；'.join(str(item) for item in hooks) if hooks else '暂无'}",
        f"- advisor_questions：{'；'.join(str(item) for item in questions) if questions else '暂无'}",
    ]


def _append_records(lines: list[str], records: list[PaperRecord], empty_text: str, limit: int | None = None) -> None:
    selected = records[:limit] if limit else records
    if not selected:
        lines.extend([empty_text, ""])
        return
    for index, record in enumerate(selected, start=1):
        lines.append(_paper_header(record, index))
        lines.extend(_basic_paper_lines(record))
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
) -> None:
    lines.extend(["## 8. 数据源健康与空报告处理", ""])
    lines.append(f"- D 类/过滤数量：{filtered_count}")
    lines.append(f"- Warning 数量：{len(warnings or [])}")
    lines.append(f"- Source health 摘要：{_source_health_brief(source_health)}")
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
) -> str:
    records = [record for record in records if record.relevance_label in {"A", "B", "C"}]
    sorted_records = _sort_by_reading_priority(records)
    high_priority = [record for record in sorted_records if reading_priority_score(record) >= 70]
    topic_counts = Counter(tag for record in records for tag in research_tags(record))
    main_topics = [topic for topic, _ in topic_counts.most_common(3)]
    source_names = sorted({record.source for record in records})
    has_mainline = any(
        set(research_tags(record)) & {"LWE", "MLWE", "Module-SIS", "Lattice Reduction", "PQC Implementation"}
        for record in records
    )
    lines: list[str] = [
        f"# 格密码科研情报日报 - {digest_date.isoformat()}",
        "",
        "## 1. 今日核心结论",
        "",
        f"- 最终入选论文数：{len(records)}",
        f"- 高优先级论文数：{len(high_priority)}",
        f"- 检索窗口：{since_window}",
        f"- 主要来源：{'、'.join(source_names[:5]) if source_names else '无'}",
        f"- 今日主题：{'、'.join(main_topics) if main_topics else '无'}",
        f"- 是否出现 AI4Lattice：{'是' if any('AI4Lattice' in research_tags(record) for record in records) else '否'}",
        f"- 是否覆盖 LWE/MLWE/Module-SIS/格基约简/PQC 实现：{'是' if has_mainline else '否'}",
        f"- 数据源健康：{_source_health_brief(source_health)}",
    ]
    if len(records) == 0:
        lines.append("今日未发现值得记录的格密码相关新论文。")
    if warnings:
        lines.append(f"- Warning：{len(warnings)} 条，详见第 8 节。")
    lines.append("")

    lines.extend(["## 2. 高优先级论文", ""])
    _append_records(lines, high_priority, "今日无高优先级论文。", limit=8)

    _append_ai_section(lines, records)
    _append_reduction_section(lines, records)
    _append_pqc_section(lines, records)
    _append_reading_queue(lines, records)
    _append_idea_and_questions(lines, records)
    _append_source_health_and_empty(lines, records, filtered_count, source_health, warnings)
    return "\n".join(lines)
