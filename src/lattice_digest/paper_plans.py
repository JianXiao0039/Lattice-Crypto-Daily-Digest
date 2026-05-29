from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from lattice_digest.ideas import TRACK_LINKS, normalize_key, sanitize, short_hash


POLLUTION_MARKERS = ("contentReference", "oaicite", "id=")


@dataclass(frozen=True)
class PaperPlanResult:
    plans: list[dict[str, Any]]
    markdown_paths: list[Path]
    json_paths: list[Path]
    obsidian_paths: list[Path]
    dry_run: bool = False


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [sanitize(item) for item in value if sanitize(item)]
    if isinstance(value, str) and value.strip():
        return [sanitize(value)]
    return []


def _score(value: object) -> int:
    try:
        return max(0, min(100, int(value or 0)))
    except (TypeError, ValueError):
        return 0


def _combined_text(idea: dict[str, Any]) -> str:
    values = [
        idea.get("title"),
        idea.get("track"),
        idea.get("core_question"),
        idea.get("intuition"),
        idea.get("minimum_viable_project"),
        idea.get("possible_contribution"),
        " ".join(_as_list(idea.get("subtracks"))),
        " ".join(_as_list(idea.get("evidence_snippets"))),
        " ".join(_as_list(idea.get("experiments_needed"))),
        " ".join(_as_list(idea.get("advisor_questions"))),
    ]
    return " ".join(sanitize(value).lower() for value in values)


def _has(text: str, *terms: str) -> bool:
    return any(term in text for term in terms)


def load_idea_bank(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    ideas = payload.get("ideas") if isinstance(payload, dict) else None
    return [dict(idea) for idea in ideas if isinstance(idea, dict)] if isinstance(ideas, list) else []


def safe_slug(value: str, *, max_length: int = 96) -> str:
    text = normalize_key(value)
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-.")
    if not text:
        text = "paper-plan"
    if len(text) > max_length:
        text = text[:max_length].rstrip("-.")
    return text


def _plan_id(idea: dict[str, Any]) -> str:
    key = str(idea.get("idea_id") or idea.get("idea_key") or idea.get("title") or "")
    return "plan-" + short_hash(key, 12)


def _maturity(idea: dict[str, Any], score: int) -> str:
    raw = sanitize(idea.get("maturity"))
    if raw in {"paper_outline_ready", "experiment_ready"}:
        return raw
    if raw in {"mvp_designable", "literature_supported"}:
        return "mvp_designable"
    if sanitize(idea.get("track")) == "ZK-friendly PQ Privacy" and score >= 70:
        return "long_term_direction"
    return "mvp_designable" if score >= 60 else "long_term_direction"


def _plan_type(track: str, text: str) -> str:
    if track == "AI4Lattice":
        return "benchmark_paper" if _has(text, "benchmark") else "experiment_paper"
    if track == "Module-SIS Primitive":
        return "construction_paper"
    if track == "ML-KEM / ML-DSA Implementation Security":
        return "implementation_artifact"
    if track == "BKZ / Lattice Reduction":
        return "benchmark_paper"
    if track == "LWE/RLWE/MLWE Cryptanalysis":
        return "security_analysis_paper"
    if track == "ZK-friendly PQ Privacy":
        return "long_term_phd_direction"
    if track == "FHE / Parameter Security":
        return "security_analysis_paper" if _has(text, "security", "parameter", "attack") else "background_only"
    if track == "PQC Systems":
        return "implementation_artifact"
    return "background_only"


def _target_horizon(plan_type: str, maturity: str, score: int) -> str:
    if plan_type == "long_term_phd_direction":
        return "phd_year_1" if score >= 75 else "long_term"
    if maturity == "paper_outline_ready" and score >= 85:
        return "3_months"
    if maturity == "experiment_ready" and score >= 75:
        return "3_months"
    if maturity == "mvp_designable" and score >= 70:
        return "6_months"
    if score >= 50:
        return "6_months"
    return "long_term"


def _priority(score: int) -> str:
    if score >= 85:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def _score_label(score: int) -> str:
    if score >= 85:
        return "优先推进"
    if score >= 70:
        return "值得推进"
    if score >= 50:
        return "备选计划"
    if score >= 30:
        return "暂存计划"
    return "不建议推进"


def paper_plan_score(idea: dict[str, Any]) -> int:
    idea_score = _score(idea.get("idea_priority_score"))
    maturity = sanitize(idea.get("maturity"))
    track = sanitize(idea.get("track"))
    text = _combined_text(idea)
    score = int(idea_score * 0.55)
    score += {
        "paper_outline_ready": 20,
        "experiment_ready": 18,
        "mvp_designable": 14,
        "literature_supported": 9,
        "vague_signal": 4,
    }.get(maturity, 5)
    score += {
        "AI4Lattice": 12,
        "LWE/RLWE/MLWE Cryptanalysis": 11,
        "BKZ / Lattice Reduction": 10,
        "Module-SIS Primitive": 11,
        "ML-KEM / ML-DSA Implementation Security": 9,
        "ZK-friendly PQ Privacy": 8,
        "FHE / Parameter Security": 5,
        "PQC Systems": 4,
        "Other": 0,
    }.get(track, 0)
    if sanitize(idea.get("minimum_viable_project")):
        score += 5
    if _as_list(idea.get("experiments_needed")):
        score += 5
    if sanitize(idea.get("implementation_artifact")):
        score += 4
    if _as_list(idea.get("proof_or_security_analysis_needed")):
        score += 4
    if _has(text, "survey", "overview", "background") and track in {"PQC Systems", "Other"}:
        score = min(score, 60)
    if track == "FHE / Parameter Security" and not _has(text, "security", "parameter", "attack", "implementation", "bootstrapping cost"):
        score = min(score, 62)
    if track == "Other":
        score = min(score, 45)
    return max(0, min(100, score))


def _source_papers(idea: dict[str, Any]) -> list[dict[str, Any]]:
    papers = idea.get("source_papers")
    if not isinstance(papers, list):
        return []
    cleaned: list[dict[str, Any]] = []
    for paper in papers:
        if not isinstance(paper, dict):
            continue
        cleaned.append(
            {
                "title": sanitize(paper.get("title")),
                "url": sanitize(paper.get("url")),
                "source_digest_date": sanitize(paper.get("source_digest_date")),
                "priority_label": sanitize(paper.get("priority_label")),
                "reading_priority_score": _score(paper.get("reading_priority_score")),
            }
        )
    return cleaned


def _common_pitfalls(track: str) -> list[str]:
    base = [
        "不要把研究计划写成已经完成的论文结论。",
        "不要夸大 toy 参数实验到真实参数安全结论。",
        "不要把关键词共现当成技术贡献。",
    ]
    if track == "AI4Lattice":
        base.append("不要把 AI 写成端到端破解黑箱，必须限定在经典攻击 pipeline 的可验证子模块。")
    if track == "Module-SIS Primitive":
        base.append("不要只把 LWE/SIS 名词替换成 Module-SIS；必须明确构造接口、安全目标和参数入口。")
    if track == "ZK-friendly PQ Privacy":
        base.append("不要一开始做大而空系统；短期 MVP 要收敛到小原语、小 benchmark 或小 artifact。")
    return base


def _reviewer_questions(track: str) -> list[str]:
    questions = [
        "创新性在哪里，和已有工作的最小差异是什么？",
        "为什么这不是关键词拼接？",
        "是否只在 toy 参数有效？",
        "能否推广到更真实的参数或更标准的 threat model？",
        "安全结论是否过度声称？",
    ]
    if track == "AI4Lattice":
        questions.extend(
            [
                "AI 模块相对于 random / heuristic / estimator baseline 的收益是否显著？",
                "模型学到的是数学现象、数据泄漏，还是已有攻击启发式的再发现？",
            ]
        )
    if track == "Module-SIS Primitive":
        questions.extend(
            [
                "correctness、binding/collision resistance 或 equivocation 目标是否定义清楚？",
                "参数估计是否足以支撑安全级别声明？",
            ]
        )
    return questions[:10]


def _track_template(track: str, idea: dict[str, Any]) -> dict[str, Any]:
    text = _combined_text(idea)
    if track == "AI4Lattice":
        return {
            "why_not_trivial": "计划把 AI 限定为 coordinate selection、sample selection、BKZ/hybrid 参数建议或 hard/easy instance separation 等 classical attack pipeline 子程序，而不是声称端到端破解 LWE。",
            "why_not_blind": "核心是定义可测量接口、classical baseline 和失败判据，避免仅把 Transformer/Swin/Mamba/GNN 与 LWE 关键词拼接。",
            "minimum_viable_paper": "构造 toy LWE / sparse LWE / RLWE / MLWE benchmark，选一个子任务做学习排序，与 random、heuristic、lattice-estimator 或简单 MLP/CNN/Transformer baseline 比较。",
            "expected_contributions": {
                "理论贡献": "不作为当前 MVP 贡献；只给出 attack interface 和假设边界。",
                "构造贡献": "一个可插入 classical attack pipeline 的学习辅助子模块定义。",
                "实验贡献": "报告 success rate、rank improvement、cost reduction、false positive rate 和 wall-clock time。",
                "实现贡献": "提供可复现训练、评估和 baseline 脚本。",
                "benchmark 贡献": "建立 toy LWE / sparse LWE / RLWE/MLWE 小规模数据集与评测协议。",
                "artifact 贡献": "最小 notebook + scripts + configs。",
                "研究叙事贡献": "把 AI4Lattice 定位为 classical cryptanalysis subroutine，而不是黑箱攻击。",
            },
            "experiment_plan": [
                "生成 toy LWE / sparse LWE / RLWE / MLWE instances。",
                "定义 coordinate selection、sample selection 或 support recovery 子任务。",
                "对接 BKZ/hybrid attack parameter guidance 或 estimator sanity check。",
                "比较 random、classical heuristic、simple MLP/CNN/Transformer/Swin/Mamba/GNN baseline。",
                "用 success rate、rank improvement、cost reduction、wall-clock time 和 false positive rate 做评价。",
            ],
            "baseline_methods": ["random baseline", "classical heuristic", "lattice-estimator", "simple MLP/CNN/Transformer"],
            "datasets_or_instances": ["toy LWE", "sparse LWE", "small RLWE/MLWE", "synthetic attack traces"],
            "evaluation_metrics": ["success rate", "rank improvement", "cost reduction", "wall-clock time", "false positive rate"],
        }
    if track == "Module-SIS Primitive":
        return {
            "why_not_trivial": "计划必须给出 Module-SIS 原语接口、correctness、安全目标、参数估计和 artifact，而不是把 SIS/LWE 名词换成新标题。",
            "why_not_blind": "重点是解释构造逻辑、collision generation / binding / equivocation 边界，以及与 lattice commitment 或 chameleon hash 的差异。",
            "minimum_viable_paper": "完成 keygen/hash/adapt/verify 或 commitment/open/verify 的最小 Sage/Python prototype，给出 correctness check、参数表和安全估计。",
            "expected_contributions": {
                "理论贡献": "定义安全目标并给出证明入口；完整证明视难度推进。",
                "构造贡献": "一个收敛的小原语接口，如 Module-SIS commitment 或 chameleon hash。",
                "实验贡献": "参数估计和 correctness / collision generation benchmark。",
                "实现贡献": "Sage/Python prototype。",
                "benchmark 贡献": "与已有 lattice-based commitments / chameleon hashes 的参数对照。",
                "artifact 贡献": "可复现参数脚本和测试向量。",
                "研究叙事贡献": "服务短期可投稿小原语与长期 PQ privacy primitive 主线。",
            },
            "experiment_plan": [
                "实现 Sage/Python prototype。",
                "测试 keygen/hash/adapt/verify 或 commitment/open/verify correctness。",
                "评估 collision generation correctness 和运行时间。",
                "做 Module-SIS 参数估计与安全级别 sanity check。",
                "和已有 lattice-based commitments 或 chameleon hashes 做参数/接口对比。",
            ],
            "baseline_methods": ["existing lattice commitment", "existing lattice chameleon hash", "parameter estimator"],
            "datasets_or_instances": ["synthetic Module-SIS parameter sets", "toy correctness vectors"],
            "evaluation_metrics": ["correctness", "runtime", "key/signature/hash size", "estimated security level"],
        }
    if track == "ML-KEM / ML-DSA Implementation Security":
        return {
            "why_not_trivial": "计划围绕明确 implementation audit、constant-time、side-channel、fault、rejection sampling leakage 或 FO transform 实现风险展开，而不是泛泛说 PQC 安全。",
            "why_not_blind": "必须定义 target implementation、漏洞模型、验证目标和 mitigation checklist。",
            "minimum_viable_paper": "选一个公开 ML-KEM/ML-DSA/Kyber/Dilithium/Falcon 实现，完成最小 audit checklist、timing/constant-time 或 fault/leakage case study。",
            "expected_contributions": {
                "理论贡献": "不作为当前 MVP 贡献；重点是 threat model 和安全工程边界。",
                "构造贡献": "不作为当前 MVP 贡献。",
                "实验贡献": "复现 leakage/fault/audit case 或验证 countermeasure。",
                "实现贡献": "audit scripts、test vectors 和 benchmark。",
                "benchmark 贡献": "production hardening checklist。",
                "artifact 贡献": "可运行的 implementation security artifact。",
                "研究叙事贡献": "连接系统安全与 PQC 落地。",
            },
            "experiment_plan": [
                "确定 target implementation。",
                "做 constant-time / timing check。",
                "定义 side-channel 或 fault model。",
                "检查 rejection sampling leakage、decryption failure handling 或 FO transform implementation。",
                "生成 test vectors、benchmark 和 production audit checklist。",
            ],
            "baseline_methods": ["reference implementation", "hardened implementation", "constant-time checker"],
            "datasets_or_instances": ["test vectors", "timing traces", "fault/leakage scenarios"],
            "evaluation_metrics": ["leakage evidence", "constant-time violations", "fault success rate", "overhead"],
        }
    if track == "BKZ / Lattice Reduction":
        return {
            "why_not_trivial": "计划聚焦 BKZ/LLL/fplll/G6K、estimator、block-size sweep、pruning/enumeration 参数或 attack cost sanity check。",
            "why_not_blind": "AI 若出现，只作为辅助调度、参数建议或预测模块，不能替代 classical reduction baseline。",
            "minimum_viable_paper": "复现小规模 LLL/BKZ baseline，做 block-size sweep、GSA deviation 和 estimator comparison。",
            "expected_contributions": {
                "理论贡献": "不作为当前 MVP 贡献；可整理 cost model 假设。",
                "构造贡献": "不作为当前 MVP 贡献。",
                "实验贡献": "BKZ/G6K/fplll 参数敏感性和 cost sanity check。",
                "实现贡献": "可复现 scripts 和 configs。",
                "benchmark 贡献": "lattice reduction / hybrid attack tuning benchmark。",
                "artifact 贡献": "fplll/G6K/estimator 对接 artifact。",
                "研究叙事贡献": "为 AI-assisted attack pipeline 提供 classical baseline。",
            },
            "experiment_plan": [
                "建立 LLL/BKZ baseline。",
                "对接 fplll/G6K。",
                "做 block size sweep。",
                "分析 GSA deviation、pruning/enumeration parameters。",
                "和 lattice-estimator 做 cost model sanity check。",
            ],
            "baseline_methods": ["LLL", "BKZ", "fplll", "G6K", "lattice-estimator"],
            "datasets_or_instances": ["toy lattice instances", "LWE-derived lattices", "hybrid attack parameter grids"],
            "evaluation_metrics": ["root Hermite factor", "runtime", "node count", "cost estimate", "success rate"],
        }
    if track == "ZK-friendly PQ Privacy":
        return {
            "why_not_trivial": "该方向不是申博包装，而是可连接 lattice commitments、ZK-friendly hashing、anonymous credentials、privacy-preserving authentication、linkable ring signatures 和 post-quantum identity 的长期研究线。",
            "why_not_blind": "短期必须收敛到一个可验证小原语、小 benchmark 或小实现 artifact，避免一开始写成大系统愿景。",
            "minimum_viable_paper": "选择 commitment / hash / credential / anonymous authentication 中一个小接口，分析 ZK-friendly encoding、PQ assumption mapping 和参数可行性。",
            "expected_contributions": {
                "理论贡献": "定义安全目标、PQ assumption mapping 和 ZK compatibility 边界。",
                "构造贡献": "一个小型 lattice commitment / hash / credential 组件草案。",
                "实验贡献": "参数和 constraint-friendliness sanity check。",
                "实现贡献": "最小 prototype 或 encoding benchmark。",
                "benchmark 贡献": "ZK-friendly primitive feasibility table。",
                "artifact 贡献": "toy implementation 和参数脚本。",
                "研究叙事贡献": "形成长期 PQ privacy / identity research line。",
            },
            "experiment_plan": [
                "选定 commitment / hash / credential / anonymous authentication toy construction。",
                "分析 constraint-friendliness 和 proof-system compatibility assumptions。",
                "映射 post-quantum security assumption。",
                "做参数和实现可行性 sanity check。",
                "规划长期 protocol integration path。",
            ],
            "baseline_methods": ["lattice commitment", "ZK-friendly hash", "anonymous credential primitive"],
            "datasets_or_instances": ["toy parameter sets", "constraint count examples"],
            "evaluation_metrics": ["constraint count", "key/proof size", "runtime", "security assumption clarity"],
        }
    return {
        "why_not_trivial": "计划只作为保守研究草案，推进前必须确认它和格密码主线的真实关系。",
        "why_not_blind": "避免把泛 PQC / FHE / systems / background 线索包装成核心格密码贡献。",
        "minimum_viable_paper": sanitize(idea.get("minimum_viable_project")) or "TODO_VERIFY：需要先补读来源论文，再定义 MVP。",
        "expected_contributions": {
            "理论贡献": "不作为当前 MVP 贡献。",
            "构造贡献": "不作为当前 MVP 贡献。",
            "实验贡献": "若有明确参数或实现入口，可做小实验。",
            "实现贡献": "视具体来源论文决定。",
            "benchmark 贡献": "可整理 related work / parameter table。",
            "artifact 贡献": "暂不承诺。",
            "研究叙事贡献": "作为背景或长期叙事素材。",
        },
        "experiment_plan": ["TODO_VERIFY：阅读来源论文后确认是否存在可复现实验。"],
        "baseline_methods": ["TODO_VERIFY"],
        "datasets_or_instances": ["TODO_VERIFY"],
        "evaluation_metrics": ["TODO_VERIFY"],
    }


def _technical_novelty_candidates(track: str) -> list[str]:
    if track == "AI4Lattice":
        return [
            "明确 AI 模块在 classical attack pipeline 中的接口。",
            "给出可复现 benchmark 和 classical baseline。",
            "区分 toy phenomenon、leakage artifact 与真正有用的 attack subroutine。",
        ]
    if track == "Module-SIS Primitive":
        return [
            "更清晰的 Module-SIS primitive interface。",
            "可复现参数估计和 correctness artifact。",
            "与 commitment/chameleon hash 现有构造的接口和参数对照。",
        ]
    if track == "ZK-friendly PQ Privacy":
        return [
            "把 PQ privacy primitive 收敛为可验证小接口。",
            "连接 lattice commitment 与 ZK-friendly encoding。",
            "给出长期 protocol integration path 但短期只做小 artifact。",
        ]
    return ["可复现 artifact", "参数或实现 sanity check", "更清楚的研究边界。"]


def _repo_structure(track: str) -> list[str]:
    base = ["artifact/", "src/", "experiments/", "data/", "configs/", "notebooks/", "scripts/", "tests/", "docs/", "results/", "README.md"]
    if track == "Module-SIS Primitive":
        base.extend(["sage/", "parameters/"])
    if track == "ML-KEM / ML-DSA Implementation Security":
        base.extend(["targets/", "audit/", "vectors/"])
    if track in {"AI4Lattice", "BKZ / Lattice Reduction"}:
        base.extend(["baselines/", "models/", "estimators/"])
    return base


def create_paper_plan(idea: dict[str, Any]) -> dict[str, Any]:
    track = sanitize(idea.get("track")) or "Other"
    text = _combined_text(idea)
    score = paper_plan_score(idea)
    maturity = _maturity(idea, score)
    plan_type = _plan_type(track, text)
    template = _track_template(track, idea)
    plan_id = _plan_id(idea)
    title = sanitize(idea.get("title")) or "Untitled idea"
    source_papers = _source_papers(idea)
    advisor_questions = _as_list(idea.get("advisor_questions")) or ["这个计划是否值得作为 3-6 个月论文推进？"]
    warnings = [
        "这是研究计划草案，不是论文结论。",
        "不得声称已有实验结果或安全证明。",
    ]
    if not source_papers:
        warnings.append("缺少 source_papers，相关论文阅读清单需要 TODO_VERIFY。")
    plan = {
        "plan_id": plan_id,
        "source_idea_id": sanitize(idea.get("idea_id")),
        "title": title,
        "tentative_paper_title": f"{title}：一个保守可验证的研究计划",
        "track": track,
        "subtracks": _as_list(idea.get("subtracks")),
        "plan_type": plan_type,
        "maturity": maturity,
        "priority": _priority(score),
        "paper_plan_score": score,
        "paper_plan_label": _score_label(score),
        "target_horizon": _target_horizon(plan_type, maturity, score),
        "core_research_question": sanitize(idea.get("core_question")) or "TODO_VERIFY：需要从来源论文中确认核心研究问题。",
        "why_this_is_not_trivial": template["why_not_trivial"],
        "why_this_is_not_blind_combination": template["why_not_blind"],
        "minimum_viable_paper": template["minimum_viable_paper"],
        "expected_contributions": template["expected_contributions"],
        "technical_novelty_candidates": _technical_novelty_candidates(track),
        "experiment_plan": template["experiment_plan"],
        "implementation_plan": [
            sanitize(idea.get("implementation_artifact")) or "优先实现最小可复现实验，不先承诺 production-grade system。",
            "写 README、configs、tests 和 exact reproduction command。",
        ],
        "proof_or_security_analysis_plan": _as_list(idea.get("proof_or_security_analysis_needed"))
        or ["需要证明或分析安全目标、攻击模型、参数假设和失败边界。"],
        "parameter_analysis_plan": [
            "列出 toy / medium / target-like 三档参数。",
            "用 estimator、参数脚本或 existing benchmarks 做 sanity check。",
            "明确哪些结论只适用于 toy regime。",
        ],
        "baseline_methods": template["baseline_methods"],
        "datasets_or_instances": template["datasets_or_instances"],
        "evaluation_metrics": template["evaluation_metrics"],
        "reproducibility_artifact": "最小可复现 artifact：代码、参数、配置、实验日志和 README。",
        "repository_structure": _repo_structure(track),
        "related_work_to_read": source_papers or [{"title": "TODO_VERIFY", "url": "", "note": "Idea 缺少来源论文，不能编造 related work。"}],
        "risks": _as_list(idea.get("risks")) or ["实验不显著风险", "与已有工作重复风险", "安全证明难度风险"],
        "common_pitfalls": _common_pitfalls(track),
        "advisor_questions": advisor_questions[:10],
        "reviewer_questions": _reviewer_questions(track),
        "rebuttal_preparation": [
            "提前准备和最接近 related work 的差异表。",
            "明确所有实验只支持哪些有限结论。",
            "准备 negative results 或降级贡献说明。",
        ],
        "three_month_execution_plan": {
            "Week 1-2": ["补读来源论文和 3-5 篇 nearest related work。", "写 MVP spec 和 threat/model boundary。"],
            "Week 3-4": ["实现最小 prototype 或 benchmark。", "跑第一轮 baseline。"],
            "Month 2": ["扩展实验矩阵或参数分析。", "整理组会汇报材料。"],
            "Month 3": ["补安全分析或 proof sketch。", "写 short paper / workshop draft。"],
        },
        "next_7_days": [
            "核对来源论文，不补事实、不编造结论。",
            "写一页 MVP 设计。",
            "列出 baseline 和第一批参数。",
        ],
        "next_30_days": [
            "完成最小 prototype。",
            "跑可复现实验或参数估计。",
            "和导师确认投稿定位或是否降级为 artifact/benchmark。",
        ],
        "long_term_research_path": [
            "硕士阶段：收敛到可验证小贡献和 artifact。",
            "PhD 前两年：扩展为系统化 lattice/PQC/AI-assisted cryptanalysis 研究线。",
            "PhD 后期及后续：发展到 privacy-preserving PQ systems、lattice primitives 或 cryptanalysis infrastructure。",
        ],
        "phd_narrative_connection": _phd_narrative(track),
        "source_papers": source_papers,
        "obsidian_links": TRACK_LINKS.get(track, []),
        "tags": ["paper_plan", normalize_key(track).replace(" ", "_").replace("/", "_")],
        "created_from": ["idea_bank"],
        "created_at": date.today().isoformat(),
        "warnings": warnings,
    }
    return plan


def _phd_narrative(track: str) -> str:
    if track == "ZK-friendly PQ Privacy":
        return (
            "该方向可以连接 lattice commitments、post-quantum anonymous credentials、ZK-friendly cryptographic encodings、"
            "privacy-preserving authentication 和 post-quantum identity systems。它不只是申请材料中的叙事点，"
            "也可以发展成长期可扩展研究方向；但短期 MVP 必须收敛到小原语、小 benchmark 或小实现 artifact。"
        )
    if track == "AI4Lattice":
        return "该方向可把硕士阶段的 AI-assisted lattice cryptanalysis artifact 扩展为 PhD 阶段的 cryptanalytic infrastructure 与 attack-pipeline optimization 主线。"
    if track == "Module-SIS Primitive":
        return "该方向可支撑短期小原语论文，并延展到 lattice commitments、privacy primitives 和 PQ protocol components。"
    return "该计划可作为格密码/PQC 研究叙事的一个模块，是否上升为 PhD 主线需要由实验显著性和理论边界决定。"


def select_ideas(
    ideas: list[dict[str, Any]],
    *,
    top: int = 5,
    min_idea_score: int = 70,
    tracks: set[str] | None = None,
    maturities: set[str] | None = None,
    limit: int | None = None,
    single_idea_id: str | None = None,
) -> list[dict[str, Any]]:
    selected = []
    for idea in ideas:
        if single_idea_id and sanitize(idea.get("idea_id")) != single_idea_id:
            continue
        if _score(idea.get("idea_priority_score")) < min_idea_score:
            continue
        if tracks and sanitize(idea.get("track")) not in tracks:
            continue
        if maturities and sanitize(idea.get("maturity")) not in maturities:
            continue
        selected.append(idea)
    selected.sort(key=lambda item: (-_score(item.get("idea_priority_score")), sanitize(item.get("title")).lower()))
    max_count = limit if limit is not None else top
    return selected[:max_count] if max_count else selected


def _lines(items: list[str], empty: str = "TODO_VERIFY") -> list[str]:
    values = [sanitize(item) for item in items if sanitize(item)]
    if not values:
        values = [empty]
    return [f"- {item}" for item in values]


def _dict_lines(items: dict[str, str]) -> list[str]:
    return [f"- {key}：{sanitize(value)}" for key, value in items.items()]


def _paper_lines(papers: list[dict[str, Any]]) -> list[str]:
    if not papers:
        return ["- TODO_VERIFY：当前 idea 未提供 source_papers，必须回到 digest / paper card 核验。"]
    lines = []
    for paper in papers:
        title = sanitize(paper.get("title")) or "unknown"
        url = sanitize(paper.get("url"))
        score = paper.get("reading_priority_score", "")
        label = sanitize(paper.get("priority_label"))
        ref = f"[{title}]({url})" if url else title
        lines.append(f"- {ref}；digest={paper.get('source_digest_date', '')}；priority={label}/{score}")
    return lines


def render_markdown(plan: dict[str, Any], *, obsidian: bool = False) -> str:
    links = " ".join(_as_list(plan.get("obsidian_links"))) if obsidian else ""
    lines = [f"# Paper Plan: {sanitize(plan.get('title'))}", ""]
    if links:
        lines.extend([links, ""])
    lines.extend(
        [
            "## 1. 计划摘要",
            "",
            f"- 来源 idea：{plan.get('source_idea_id') or 'TODO_VERIFY'}",
            f"- Track：{plan.get('track')}",
            f"- Plan Type：{plan.get('plan_type')}",
            f"- Score：{plan.get('paper_plan_score')} / {plan.get('paper_plan_label')}",
            f"- Priority：{plan.get('priority')}",
            f"- Target Horizon：{plan.get('target_horizon')}",
            "",
            "## 2. 核心研究问题",
            "",
            f"- 要解决的问题：{plan.get('core_research_question')}",
            "- 为什么有意义：它必须服务格密码、PQC、AI4Lattice、实现安全或后量子隐私原语中的明确问题。",
            f"- 最小可研究对象：{plan.get('minimum_viable_paper')}",
            "",
            "## 3. 为什么不是平庸拼接",
            "",
            f"- 非平庸性：{plan.get('why_this_is_not_trivial')}",
            f"- 非盲目组合：{plan.get('why_this_is_not_blind_combination')}",
            "",
            "## 4. 最低可做版本",
            "",
            f"- MVP：{plan.get('minimum_viable_paper')}",
            "- 最小证明或安全分析：只写需要证明/需要分析，不声称已经完成。",
            "- 最小 artifact：代码、配置、参数和复现实验命令。",
            "- 最小可投稿贡献：如果主结果不显著，降级为 artifact / benchmark / workshop。",
            "",
            "## 5. 预期贡献点",
            "",
        ]
    )
    lines.extend(_dict_lines(plan.get("expected_contributions", {})))
    lines.extend(["", "## 6. 技术路线", ""])
    lines.extend(
        [
            "1. 输入材料：来源论文、idea evidence、参数设定和 nearest related work。",
            "2. 建模方式：先定义最小接口和 threat/model boundary。",
            "3. 算法或构造：只实现 MVP 必需部分。",
            "4. 实验或证明：优先做可复现 baseline 和安全分析入口。",
            "5. 结果分析：区分有效、无效和只在 toy regime 有效。",
            "6. 失败时的降级方案：转为 benchmark、artifact、negative result 或 related work survey。",
            "",
            "## 7. 实验路线",
            "",
        ]
    )
    lines.extend(_lines(plan.get("experiment_plan", [])))
    lines.extend(["", "## 8. 证明或安全分析路线", ""])
    lines.extend(_lines(plan.get("proof_or_security_analysis_plan", [])))
    lines.extend(["- 必须指出安全证明难点，不能声称已经证明。", "", "## 9. Artifact 与代码目录", ""])
    lines.extend(_lines(plan.get("repository_structure", [])))
    lines.extend(["", "## 10. 相关论文阅读清单", ""])
    lines.extend(_paper_lines(plan.get("related_work_to_read", [])))
    lines.extend(["", "## 11. 3 个月执行计划", ""])
    three_month = plan.get("three_month_execution_plan", {})
    if isinstance(three_month, dict):
        for phase, tasks in three_month.items():
            lines.append(f"### {phase}")
            lines.extend(_lines(tasks))
            lines.append("")
    lines.extend(["## 12. 风险与降级方案", ""])
    lines.extend(_lines(plan.get("risks", [])))
    lines.extend(_lines(plan.get("common_pitfalls", [])))
    lines.extend(
        [
            "- 降级方案：如果核心贡献不成立，降级成 workshop / artifact / benchmark / survey+experiment。",
            "",
            "## 13. 导师讨论问题",
            "",
        ]
    )
    lines.extend(_lines(plan.get("advisor_questions", [])))
    lines.extend(["", "## 14. 模拟审稿人质疑", ""])
    lines.extend(_lines(plan.get("reviewer_questions", [])))
    lines.extend(["", "## 15. PhD 与长期研究规划连接", ""])
    lines.extend(
        [
            f"- 硕士阶段短期产出：{plan.get('minimum_viable_paper')}",
            "- PhD 前两年：扩展为更系统的 lattice/PQC research line。",
            "- PhD 后期及后续：围绕可复现 artifact、隐私系统、实现安全或 cryptanalysis infrastructure 延展。",
            f"- 方向连接：{plan.get('phd_narrative_connection')}",
            "",
            "## 16. 下一步行动清单",
            "",
            "### 今天能做",
        ]
    )
    lines.extend(_lines(plan.get("next_7_days", [])[:2]))
    lines.extend(["", "### 本周能做"])
    lines.extend(_lines(plan.get("next_7_days", [])))
    lines.extend(["", "### 需要补读"])
    lines.extend(_paper_lines(plan.get("source_papers", [])))
    lines.extend(["", "### 需要写代码"])
    lines.extend(_lines(plan.get("implementation_plan", [])))
    lines.extend(["", "### 需要问导师"])
    lines.extend(_lines(plan.get("advisor_questions", [])[:5]))
    lines.extend(["", "### 需要验证的关键假设"])
    lines.extend(_lines(plan.get("warnings", [])))
    lines.append("")
    text = "\n".join(lines)
    for marker in POLLUTION_MARKERS:
        text = text.replace(marker, "")
    text = re.sub(r"<[^>]+>", "", text)
    return text


def _unique_path(path: Path, *, force: bool) -> Path:
    if force or not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    candidate = path.with_name(f"{stem}__new{suffix}")
    index = 2
    while candidate.exists():
        candidate = path.with_name(f"{stem}__new-{index}{suffix}")
        index += 1
    return candidate


def write_plan(plan: dict[str, Any], output_dir: Path, obsidian_dir: Path, *, force: bool = False) -> tuple[Path, Path, Path]:
    slug = safe_slug(f"{plan['paper_plan_score']}-{plan['track']}-{plan['title']}")
    markdown_path = _unique_path(output_dir / f"{slug}.md", force=force)
    json_path = _unique_path(output_dir / f"{slug}.json", force=force)
    obsidian_path = _unique_path(obsidian_dir / f"{slug}.md", force=force)
    output_dir.mkdir(parents=True, exist_ok=True)
    obsidian_dir.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(plan), encoding="utf-8")
    obsidian_path.write_text(render_markdown(plan, obsidian=True), encoding="utf-8")
    return markdown_path, json_path, obsidian_path


def generate_paper_plans(
    idea_bank: Path,
    output_dir: Path,
    obsidian_dir: Path,
    *,
    top: int = 5,
    min_idea_score: int = 70,
    tracks: set[str] | None = None,
    maturities: set[str] | None = None,
    dry_run: bool = False,
    force: bool = False,
    limit: int | None = None,
    single_idea_id: str | None = None,
) -> PaperPlanResult:
    ideas = load_idea_bank(idea_bank)
    selected = select_ideas(
        ideas,
        top=top,
        min_idea_score=min_idea_score,
        tracks=tracks,
        maturities=maturities,
        limit=limit,
        single_idea_id=single_idea_id,
    )
    plans = [create_paper_plan(idea) for idea in selected]
    plans.sort(key=lambda item: (-_score(item.get("paper_plan_score")), sanitize(item.get("title")).lower()))
    markdown_paths: list[Path] = []
    json_paths: list[Path] = []
    obsidian_paths: list[Path] = []
    if not dry_run:
        for plan in plans:
            markdown_path, json_path, obsidian_path = write_plan(plan, output_dir, obsidian_dir, force=force)
            markdown_paths.append(markdown_path)
            json_paths.append(json_path)
            obsidian_paths.append(obsidian_path)
    return PaperPlanResult(plans, markdown_paths, json_paths, obsidian_paths, dry_run)


def _parse_csv(value: str | None) -> set[str] | None:
    if not value:
        return None
    items = {item.strip() for item in value.split(",") if item.strip()}
    return items or None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upgrade Idea Bank entries into conservative paper plans.")
    parser.add_argument("--idea-bank", type=Path, default=Path("exports/ideas/idea-bank.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("exports/paper_plans"))
    parser.add_argument("--obsidian-dir", type=Path, default=Path("exports/obsidian/paper_plans"))
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--min-idea-score", type=int, default=70)
    parser.add_argument("--tracks", default=None)
    parser.add_argument("--maturity", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--single-idea-id", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.idea_bank.exists():
        print(f"idea bank not found: {args.idea_bank}")
        return 1
    result = generate_paper_plans(
        args.idea_bank,
        args.output_dir,
        args.obsidian_dir,
        top=args.top,
        min_idea_score=args.min_idea_score,
        tracks=_parse_csv(args.tracks),
        maturities=_parse_csv(args.maturity),
        dry_run=args.dry_run,
        force=args.force,
        limit=args.limit,
        single_idea_id=args.single_idea_id,
    )
    prefix = "DRY RUN: would generate" if args.dry_run else "generated"
    print(f"{prefix} {len(result.plans)} paper plan(s).")
    for plan in result.plans[:10]:
        print(f"- {plan['paper_plan_score']} | {plan['track']} | {plan['target_horizon']} | {plan['title']}")
    if not args.dry_run:
        for path in result.markdown_paths + result.json_paths + result.obsidian_paths:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
