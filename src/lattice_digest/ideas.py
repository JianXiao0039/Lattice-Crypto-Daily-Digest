from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from lattice_digest.audit import stable_id


TRACKS = (
    "AI4Lattice",
    "LWE/RLWE/MLWE Cryptanalysis",
    "BKZ / Lattice Reduction",
    "Module-SIS Primitive",
    "ML-KEM / ML-DSA Implementation Security",
    "PQC Systems",
    "FHE / Parameter Security",
    "ZK-friendly PQ Privacy",
    "Other",
)

TRACK_LINKS = {
    "AI4Lattice": ["[[AI4Lattice]]", "[[LWE]]", "[[BKZ]]"],
    "LWE/RLWE/MLWE Cryptanalysis": ["[[LWE]]", "[[RLWE]]", "[[MLWE]]", "[[Sparse LWE]]", "[[Dual Attack]]", "[[Primal Attack]]", "[[Hybrid Attack]]"],
    "BKZ / Lattice Reduction": ["[[BKZ]]", "[[LLL]]", "[[G6K]]", "[[fplll]]", "[[Hybrid Attack]]"],
    "Module-SIS Primitive": ["[[Module-SIS]]", "[[Chameleon Hash]]", "[[Commitment]]"],
    "ML-KEM / ML-DSA Implementation Security": ["[[ML-KEM]]", "[[ML-DSA]]", "[[Kyber]]", "[[Dilithium]]"],
    "PQC Systems": ["[[PQC Systems]]", "[[ML-KEM]]", "[[ML-DSA]]"],
    "FHE / Parameter Security": ["[[FHE]]", "[[LWE]]", "[[RLWE]]"],
    "ZK-friendly PQ Privacy": ["[[Commitment]]", "[[Module-SIS]]", "[[PQC Systems]]"],
    "Other": [],
}

POLLUTION_MARKERS = ("contentReference", "oaicite", "id=")


@dataclass(frozen=True)
class IdeaBankResult:
    ideas: list[dict[str, Any]]
    json_path: Path
    markdown_path: Path
    obsidian_path: Path
    dry_run: bool = False


def sanitize(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"<[^>]+>", "", text)
    for marker in POLLUTION_MARKERS:
        text = text.replace(marker, "")
    return re.sub(r"\s+", " ", text).strip()


def normalize_key(value: str) -> str:
    text = sanitize(value).lower()
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def short_hash(value: str, length: int = 10) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def idea_key(track: str, core_question: str) -> str:
    return f"{track.lower()}:{short_hash(normalize_key(core_question), 16)}"


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [sanitize(item) for item in value if sanitize(item)]
    if isinstance(value, str) and value.strip():
        return [sanitize(value)]
    return []


def _score(record: dict[str, Any]) -> int:
    try:
        return int(record.get("reading_priority_score") or record.get("relevance_score") or 0)
    except (TypeError, ValueError):
        return 0


def _record_date(payload: dict[str, Any], path: Path) -> str:
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        value = str(metadata.get("target_date") or metadata.get("run_date") or "").strip()
        if value:
            return value[:10]
    return path.stem


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _date_allowed(day: str, from_date: date | None, to_date: date | None) -> bool:
    try:
        parsed = date.fromisoformat(day[:10])
    except ValueError:
        return True
    if from_date and parsed < from_date:
        return False
    if to_date and parsed > to_date:
        return False
    return True


def load_digest_records(input_path: Path, from_date: date | None = None, to_date: date | None = None) -> list[dict[str, Any]]:
    paths = sorted(input_path.glob("*.json")) if input_path.is_dir() else [input_path]
    records: list[dict[str, Any]] = []
    for path in paths:
        payload = _load_json(path)
        if not payload:
            continue
        digest_date = _record_date(payload, path)
        if not _date_allowed(digest_date, from_date, to_date):
            continue
        raw_records = payload.get("records")
        if not isinstance(raw_records, list):
            continue
        for raw in raw_records:
            if isinstance(raw, dict):
                record = dict(raw)
                record["source_digest_date"] = digest_date
                records.append(record)
    return records


def _combined_text(record: dict[str, Any]) -> str:
    values = [
        record.get("title"),
        record.get("abstract"),
        record.get("reason_for_priority"),
        " ".join(_as_list(record.get("research_tags") or record.get("tags"))),
        " ".join(_as_list(record.get("research_hooks"))),
        " ".join(_as_list(record.get("advisor_questions"))),
    ]
    return " ".join(sanitize(value).lower() for value in values)


def _has(text: str, *terms: str) -> bool:
    return any(term in text for term in terms)


def classify_track(record: dict[str, Any]) -> tuple[str, list[str]]:
    text = _combined_text(record)
    has_crypto = _has(
        text,
        "lwe",
        "rlwe",
        "mlwe",
        "lattice",
        "bkz",
        "cryptanalysis",
        "module-sis",
        "kyber",
        "ml-kem",
        "dilithium",
        "ml-dsa",
    )
    has_ai = _has(
        text,
        "transformer",
        "swin",
        "mamba",
        "vmamba",
        "gnn",
        "cnn",
        "diffusion",
        "reinforcement learning",
        "bayesian optimization",
        "learning-to-rank",
        "self-supervised",
        "neural",
        "machine learning",
    )
    if has_ai and has_crypto and _has(text, "cryptanalysis", "lwe", "bkz", "lattice reduction", "coordinate selection", "hybrid attack"):
        return "AI4Lattice", ["learning-guided attack pipeline"]
    if _has(text, "module-sis", "msis", "chameleon hash", "commitment", "trapdoor", "rejection sampling"):
        return "Module-SIS Primitive", ["commitment / chameleon hash"]
    if _has(text, "ml-kem", "kyber", "ml-dsa", "dilithium", "falcon", "fn-dsa") and _has(
        text,
        "implementation",
        "side-channel",
        "fault",
        "audit",
        "leakage",
        "constant-time",
        "masking",
        "production",
    ):
        return "ML-KEM / ML-DSA Implementation Security", ["implementation security"]
    if _has(text, "bkz", "lll", "g6k", "fplll", "sieving", "enumeration", "lattice reduction", "gsa"):
        return "BKZ / Lattice Reduction", ["attack cost model"]
    if _has(text, "lwe", "rlwe", "mlwe", "sparse lwe", "secret recovery", "distinguishing", "dual attack", "primal attack", "hybrid attack"):
        return "LWE/RLWE/MLWE Cryptanalysis", ["attack analysis"]
    if _has(text, "zero-knowledge", "zk", "credential", "anonymous authentication", "ring signature", "privacy") and _has(
        text,
        "lattice",
        "commitment",
        "post-quantum",
    ):
        return "ZK-friendly PQ Privacy", ["privacy primitive"]
    if _has(text, "fhe", "ckks", "bfv", "bgv", "tfhe", "bootstrapping"):
        return "FHE / Parameter Security", ["fhe / parameters"]
    if _has(text, "pqc", "post-quantum", "tls", "hybrid key exchange", "deployment", "benchmark", "migration"):
        return "PQC Systems", ["deployment / systems"]
    return "Other", []


def _maturity(record: dict[str, Any], track: str, text: str) -> str:
    hooks = _as_list(record.get("research_hooks"))
    if _has(text, "paper outline", "proof sketch"):
        return "paper_outline_ready"
    if hooks and _has(text, "experiment", "benchmark", "artifact", "reproduce", "estimator", "implementation"):
        return "experiment_ready"
    if hooks and track in {"AI4Lattice", "Module-SIS Primitive", "BKZ / Lattice Reduction"}:
        return "mvp_designable"
    if _score(record) >= 70:
        return "literature_supported"
    return "vague_signal"


def _status(score: int, maturity: str) -> str:
    if score >= 85 and maturity in {"experiment_ready", "paper_outline_ready", "mvp_designable"}:
        return "candidate"
    if score >= 70:
        return "candidate"
    if score >= 50:
        return "seed"
    if score >= 30:
        return "parked"
    return "rejected"


def _generic_survey(record: dict[str, Any]) -> bool:
    text = _combined_text(record)
    return _has(text, "survey", "overview", "tutorial", "introduction") and not _has(
        text,
        "module-sis",
        "bkz",
        "dual attack",
        "primal attack",
        "hybrid attack",
        "ai-assisted",
        "lwe attack",
    )


def idea_priority_score(record: dict[str, Any], track: str, maturity: str) -> int:
    base = min(50, max(0, _score(record) // 2))
    track_bonus = {
        "AI4Lattice": 30,
        "LWE/RLWE/MLWE Cryptanalysis": 26,
        "BKZ / Lattice Reduction": 24,
        "Module-SIS Primitive": 24,
        "ML-KEM / ML-DSA Implementation Security": 20,
        "ZK-friendly PQ Privacy": 16,
        "FHE / Parameter Security": 10,
        "PQC Systems": 8,
        "Other": 0,
    }[track]
    score = base + track_bonus
    text = _combined_text(record)
    if _as_list(record.get("research_hooks")):
        score += 8
    if _has(text, "artifact", "implementation", "code", "sage", "python", "benchmark", "reproduce"):
        score += 8
    if _has(text, "experiment", "estimator", "parameter", "simulation", "g6k", "fplll"):
        score += 7
    if _has(text, "security proof", "proof", "reduction", "collision resistance", "binding"):
        score += 5
    if _generic_survey(record):
        score = min(score, 45)
    if track == "FHE / Parameter Security" and not _has(text, "security", "parameter", "attack", "implementation", "side-channel"):
        score = min(score, 60)
    if _has(text, "speculative quantum", "quantum attack") and maturity not in {"experiment_ready", "paper_outline_ready"}:
        score = min(score, 65)
    if track == "Other":
        score = min(score, 35)
    return max(0, min(100, score))


def _score_label(score: int) -> str:
    if score >= 85:
        return "强烈推进"
    if score >= 70:
        return "重点观察"
    if score >= 50:
        return "可做 related work / 备选"
    if score >= 30:
        return "暂存"
    return "低优先级"


def _evidence(record: dict[str, Any]) -> list[str]:
    snippets: list[str] = []
    for field in ("title", "abstract", "reason_for_priority"):
        text = sanitize(record.get(field))
        if text:
            snippets.append(text[:260])
    for field in ("research_hooks", "advisor_questions"):
        for item in _as_list(record.get(field)):
            snippets.append(item[:260])
    return list(dict.fromkeys(snippets))[:6]


def _source_paper(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": sanitize(record.get("title") or "unknown"),
        "url": sanitize(record.get("url") or record.get("source_url") or ""),
        "source_digest_date": sanitize(record.get("source_digest_date") or ""),
        "priority_label": sanitize(record.get("priority_label") or ""),
        "reading_priority_score": _score(record),
    }


def _template_fields(track: str) -> dict[str, Any]:
    if track == "AI4Lattice":
        return {
            "core_question": "能否把学习模型作为经典格攻击 pipeline 的子程序，而不是端到端破解 LWE？",
            "intuition": "把模型用于 coordinate/sample ranking、BKZ 参数建议或 hard/easy instance separation。",
            "minimum_viable_project": "构造 toy LWE/BKZ benchmark，比较学习排序与经典启发式 baseline。",
            "possible_contribution": "一个可复现的 AI-assisted lattice cryptanalysis subroutine。",
            "experiments_needed": ["toy LWE benchmark", "classical baseline", "ablation on model role"],
        }
    if track == "Module-SIS Primitive":
        return {
            "core_question": "能否把线索转化为 Module-SIS commitment / chameleon hash 小原语？",
            "intuition": "围绕 trapdoor、collision generation、binding/equivocation 和参数估计做紧凑构造。",
            "minimum_viable_project": "写出 construction sketch，给出参数表和 Sage/Python 可复现实验。",
            "possible_contribution": "短期可投稿的 lattice primitive + reproducibility artifact。",
            "experiments_needed": ["parameter estimation", "correctness checks", "comparison with lattice commitments"],
        }
    if track == "BKZ / Lattice Reduction":
        return {
            "core_question": "能否把攻击成本模型或 BKZ/G6K/fplll 线索转成可复现实验 baseline？",
            "intuition": "用透明参数估计连接 classical attack pipeline 与后续 AI-assisted subroutine。",
            "minimum_viable_project": "复现实验参数，跑 estimator/G6K/fplll 小规模对照。",
            "possible_contribution": "一个可复现 attack-cost artifact 或 hybrid attack tuning benchmark。",
            "experiments_needed": ["estimator script", "BKZ/G6K baseline", "parameter sensitivity analysis"],
        }
    if track == "ML-KEM / ML-DSA Implementation Security":
        return {
            "core_question": "实现细节是否引入 ML-KEM/ML-DSA 的可利用安全风险？",
            "intuition": "围绕 side-channel、fault、constant-time、masking 或 production audit 做系统安全叙事。",
            "minimum_viable_project": "复现一个最小 leakage/fault/audit case，并整理 mitigation checklist。",
            "possible_contribution": "PQC implementation security case study 或 benchmark artifact。",
            "experiments_needed": ["implementation audit", "leakage/fault model", "countermeasure evaluation"],
        }
    return {
        "core_question": "这条线索能否服务格密码主线、组会汇报或 related work？",
        "intuition": "先作为背景储备，避免过早承诺为论文主线。",
        "minimum_viable_project": "整理 related work 表格，并确认是否有可复现实验或参数分析入口。",
        "possible_contribution": "背景 citation bank 或长期 PhD narrative 素材。",
        "experiments_needed": ["literature check", "risk assessment"],
    }


def idea_from_record(record: dict[str, Any], hook: str | None = None) -> dict[str, Any]:
    track, subtracks = classify_track(record)
    text = _combined_text(record)
    template = _template_fields(track)
    source_title = sanitize(record.get("title") or "unknown")
    hook_text = sanitize(hook or "")
    title = hook_text or f"从《{source_title}》提炼一个保守研究 seed"
    if track == "Other" and not hook_text:
        title = f"背景储备：{source_title}"
    maturity = _maturity(record, track, text)
    score = idea_priority_score(record, track, maturity)
    core_question = hook_text or template["core_question"]
    key = idea_key(track, core_question)
    today = date.today().isoformat()
    advisor_questions = _as_list(record.get("advisor_questions")) or ["需要和导师确认该线索是否值得投入。"]
    idea = {
        "idea_id": "idea-" + short_hash(key),
        "idea_key": key,
        "title": title,
        "status": _status(score, maturity),
        "maturity": maturity,
        "track": track,
        "subtracks": subtracks,
        "idea_priority_score": score,
        "idea_priority_label": _score_label(score),
        "source_papers": [_source_paper(record)],
        "evidence_snippets": _evidence(record),
        "core_question": core_question,
        "intuition": template["intuition"],
        "minimum_viable_project": template["minimum_viable_project"],
        "possible_contribution": template["possible_contribution"],
        "experiments_needed": template["experiments_needed"],
        "proof_or_security_analysis_needed": [
            "明确安全目标、攻击模型、参数假设和 proof/estimation 边界。",
        ],
        "implementation_artifact": "优先做最小 Python/Sage notebook 或 reproducible benchmark。",
        "risks": [
            "可能只是 toy phenomenon 或背景线索，不能夸大为真实攻击能力。",
            "metadata 可能不足，推进前必须阅读原文。",
        ],
        "common_pitfalls": [
            "不要把相关关键词当成论文结论。",
            "不要把 AI4Lattice 狭隘理解为 Swin-only。",
        ],
        "advisor_questions": advisor_questions,
        "next_actions": [
            "打开来源论文并核对摘要与贡献。",
            "判断是否能在一周内设计 MVP。",
            "列出需要补读的 3 篇 related work。",
        ],
        "obsidian_links": TRACK_LINKS.get(track, []),
        "tags": ["idea_bank", normalize_key(track).replace(" ", "_").replace("/", "_")],
        "created_from": ["daily_digest"],
        "created_at": today,
        "last_updated": today,
    }
    return idea


def ideas_from_records(records: list[dict[str, Any]], min_paper_priority: int = 50) -> list[dict[str, Any]]:
    ideas: list[dict[str, Any]] = []
    for record in records:
        if _score(record) < min_paper_priority:
            continue
        hooks = _as_list(record.get("research_hooks"))
        if hooks:
            ideas.extend(idea_from_record(record, hook) for hook in hooks[:3])
        elif sanitize(record.get("priority_label")) in {"必须精读", "建议精读"}:
            ideas.append(idea_from_record(record))
    return ideas


def _merge_unique_dicts(existing: list[dict[str, Any]], incoming: list[dict[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    seen = {tuple(str(item.get(field, "")) for field in key_fields) for item in existing}
    merged = list(existing)
    for item in incoming:
        key = tuple(str(item.get(field, "")) for field in key_fields)
        if key not in seen:
            merged.append(item)
            seen.add(key)
    return merged


def _merge_unique_strings(existing: list[str], incoming: list[str]) -> list[str]:
    return list(dict.fromkeys([*existing, *incoming]))


def merge_ideas(ideas: list[dict[str, Any]], existing_ideas: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for idea in existing_ideas or []:
        if isinstance(idea, dict):
            by_key[str(idea.get("idea_key") or idea.get("idea_id") or idea.get("title"))] = dict(idea)
    for idea in ideas:
        key = str(idea.get("idea_key"))
        current = by_key.get(key)
        if current is None:
            by_key[key] = dict(idea)
            continue
        current["source_papers"] = _merge_unique_dicts(
            current.get("source_papers", []),
            idea.get("source_papers", []),
            ("title", "url"),
        )
        current["evidence_snippets"] = _merge_unique_strings(current.get("evidence_snippets", []), idea.get("evidence_snippets", []))
        current["advisor_questions"] = _merge_unique_strings(current.get("advisor_questions", []), idea.get("advisor_questions", []))
        current["obsidian_links"] = _merge_unique_strings(current.get("obsidian_links", []), idea.get("obsidian_links", []))
        if int(idea.get("idea_priority_score", 0)) > int(current.get("idea_priority_score", 0)):
            for field in ("idea_priority_score", "idea_priority_label", "status", "maturity", "title"):
                current[field] = idea[field]
        current["last_updated"] = max(str(current.get("last_updated") or ""), str(idea.get("last_updated") or ""))
    result = list(by_key.values())
    result.sort(key=lambda item: (-int(item.get("idea_priority_score", 0)), sanitize(item.get("title")).lower()))
    return result


def load_existing_ideas(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.exists():
        return []
    payload = _load_json(path)
    ideas = payload.get("ideas") if payload else None
    return [idea for idea in ideas if isinstance(idea, dict)] if isinstance(ideas, list) else []


def _track_filter(ideas: list[dict[str, Any]], tracks: set[str] | None) -> list[dict[str, Any]]:
    if not tracks:
        return ideas
    return [idea for idea in ideas if str(idea.get("track")) in tracks]


def _paper_refs(idea: dict[str, Any]) -> str:
    refs = []
    for paper in idea.get("source_papers", [])[:3]:
        title = sanitize(paper.get("title") if isinstance(paper, dict) else "")
        url = sanitize(paper.get("url") if isinstance(paper, dict) else "")
        refs.append(f"[{title}]({url})" if url else title)
    return "；".join(refs) if refs else "暂无"


def _idea_block(idea: dict[str, Any]) -> list[str]:
    return [
        f"### {sanitize(idea.get('title'))}",
        f"- Track：{idea.get('track')}",
        f"- Score：{idea.get('idea_priority_score')} / {idea.get('idea_priority_label')}",
        f"- Status：{idea.get('status')}",
        f"- Maturity：{idea.get('maturity')}",
        f"- 核心问题：{idea.get('core_question')}",
        f"- 最低可做版本：{idea.get('minimum_viable_project')}",
        f"- 下一步动作：{'；'.join(idea.get('next_actions', [])[:3])}",
        f"- 来源论文：{_paper_refs(idea)}",
        f"- Obsidian：{' '.join(idea.get('obsidian_links', []))}",
        "",
    ]


def _section(lines: list[str], title: str, ideas: list[dict[str, Any]], empty: str, limit: int | None = None) -> None:
    lines.extend([title, ""])
    selected = ideas[:limit] if limit is not None else ideas
    if not selected:
        lines.extend([empty, ""])
        return
    for idea in selected:
        lines.extend(_idea_block(idea))


def render_markdown(ideas: list[dict[str, Any]]) -> str:
    top = ideas[:10]
    by_track = {track: [idea for idea in ideas if idea.get("track") == track] for track in TRACKS}
    low = [idea for idea in ideas if int(idea.get("idea_priority_score", 0)) < 50 or idea.get("status") in {"parked", "rejected"}]
    lines = ["# Idea Bank", ""]
    _section(lines, "## 1. 本周最值得推进的 idea", top, "暂无可推进 idea。", 10)
    _section(lines, "## 2. AI4Lattice / AI-assisted Cryptanalysis", by_track["AI4Lattice"], "暂无 AI4Lattice idea。")
    _section(lines, "## 3. LWE / RLWE / MLWE Cryptanalysis", by_track["LWE/RLWE/MLWE Cryptanalysis"], "暂无 LWE/RLWE/MLWE cryptanalysis idea。")
    _section(lines, "## 4. BKZ / Lattice Reduction / Hybrid Attack", by_track["BKZ / Lattice Reduction"], "暂无 BKZ / lattice reduction idea。")
    _section(lines, "## 5. Module-SIS / Commitment / Chameleon Hash", by_track["Module-SIS Primitive"], "暂无 Module-SIS primitive idea。")
    _section(lines, "## 6. ML-KEM / ML-DSA Implementation Security", by_track["ML-KEM / ML-DSA Implementation Security"], "暂无 implementation security idea。")
    _section(lines, "## 7. PQC Systems / Protocols", by_track["PQC Systems"], "暂无 PQC systems idea。")
    _section(lines, "## 8. FHE / Parameter Security", by_track["FHE / Parameter Security"], "暂无 FHE / parameter security idea。")
    _section(lines, "## 9. ZK-friendly Post-Quantum Privacy", by_track["ZK-friendly PQ Privacy"], "暂无 ZK-friendly PQ privacy idea。")
    _section(lines, "## 10. 暂存 / 低优先级 idea", low, "暂无暂存 idea。", 20)
    lines.extend(["## 11. 下一步行动清单", ""])
    if ideas:
        lines.extend(
            [
                "- 今日可做：打开 Top 1 idea 的来源论文，确认核心问题是否真实成立。",
                "- 本周可做：为 Top 3 idea 各写一个 MVP 草图。",
                "- 需要导师确认：哪些 idea 能支撑短期投稿，哪些更适合 PhD narrative。",
                "- 需要补论文：为每个 active/candidate idea 补 3 篇 related work。",
                "- 需要补实验：优先补可复现参数估计、toy benchmark 或 implementation artifact。",
            ]
        )
    else:
        lines.append("- 暂无 idea；建议先生成最近 7d digest 或 weekly brief。")
    lines.append("")
    return "\n".join(lines)


def write_idea_bank(
    ideas: list[dict[str, Any]],
    output_dir: Path,
    obsidian_dir: Path,
    *,
    dry_run: bool = False,
) -> tuple[Path, Path, Path]:
    json_path = output_dir / "idea-bank.json"
    markdown_path = output_dir / "idea-bank.md"
    obsidian_path = obsidian_dir / "idea-bank.md"
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        obsidian_dir.mkdir(parents=True, exist_ok=True)
        payload = {"metadata": {"last_updated": date.today().isoformat(), "total_ideas": len(ideas)}, "ideas": ideas}
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        markdown = render_markdown(ideas)
        markdown_path.write_text(markdown, encoding="utf-8")
        obsidian_path.write_text(markdown, encoding="utf-8")
    return json_path, markdown_path, obsidian_path


def generate_idea_bank(
    input_path: Path,
    output_dir: Path,
    obsidian_dir: Path,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    min_paper_priority: int = 50,
    min_idea_score: int = 0,
    existing_bank: Path | None = None,
    dry_run: bool = False,
    limit: int | None = None,
    tracks: set[str] | None = None,
) -> IdeaBankResult:
    records = load_digest_records(input_path, from_date, to_date)
    candidates = ideas_from_records(records, min_paper_priority)
    existing = load_existing_ideas(existing_bank)
    ideas = merge_ideas(candidates, existing)
    ideas = [idea for idea in ideas if int(idea.get("idea_priority_score", 0)) >= min_idea_score]
    ideas = _track_filter(ideas, tracks)
    if limit is not None:
        ideas = ideas[:limit]
    json_path, markdown_path, obsidian_path = write_idea_bank(ideas, output_dir, obsidian_dir, dry_run=dry_run)
    return IdeaBankResult(ideas, json_path, markdown_path, obsidian_path, dry_run)


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _parse_tracks(value: str | None) -> set[str] | None:
    if not value:
        return None
    tracks = {item.strip() for item in value.split(",") if item.strip()}
    return tracks or None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate long-term lattice crypto idea bank from digest records.")
    parser.add_argument("--input", type=Path, default=Path("data"))
    parser.add_argument("--from-date", default=None)
    parser.add_argument("--to-date", default=None)
    parser.add_argument("--min-paper-priority", type=int, default=50)
    parser.add_argument("--min-idea-score", type=int, default=0)
    parser.add_argument("--existing-bank", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("exports/ideas"))
    parser.add_argument("--obsidian-dir", type=Path, default=Path("exports/obsidian/ideas"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--tracks", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    existing_bank = args.existing_bank or args.output_dir / "idea-bank.json"
    result = generate_idea_bank(
        args.input,
        args.output_dir,
        args.obsidian_dir,
        from_date=_parse_date(args.from_date),
        to_date=_parse_date(args.to_date),
        min_paper_priority=args.min_paper_priority,
        min_idea_score=args.min_idea_score,
        existing_bank=existing_bank,
        dry_run=args.dry_run,
        limit=args.limit,
        tracks=_parse_tracks(args.tracks),
    )
    prefix = "DRY RUN: would generate" if args.dry_run else "generated"
    print(f"{prefix} {len(result.ideas)} idea(s).")
    for idea in result.ideas[:10]:
        print(f"- {idea['idea_priority_score']} | {idea['track']} | {idea['maturity']} | {idea['title']}")
    if not args.dry_run:
        print(result.json_path)
        print(result.markdown_path)
        print(result.obsidian_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
