from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from lattice_digest.ideas import normalize_key, sanitize, short_hash
from lattice_digest.paper_plans import safe_slug


POLLUTION_MARKERS = ("contentReference", "oaicite", "id=")


@dataclass(frozen=True)
class ArtifactResult:
    artifact_dir: Path
    files: list[Path]
    directories: list[Path]
    dry_run: bool = False
    backup_dir: Path | None = None


BASE_DIRS = [
    "configs",
    "src",
    "experiments",
    "scripts",
    "tests",
    "results",
    "docs",
    "paper",
    "notes",
]


TRACK_DIRS = {
    "Module-SIS Primitive": [
        "src/primitives",
        "src/params",
        "src/benchmark",
        "experiments/parameter_estimation",
        "experiments/correctness",
        "experiments/performance",
    ],
    "AI4Lattice": [
        "src/datasets",
        "src/models",
        "src/attacks",
        "src/baselines",
        "experiments/toy_lwe",
        "experiments/rlwe_mlwe",
        "experiments/hybrid_attack",
        "configs/model",
        "configs/attack",
        "results/curves",
    ],
    "LWE/RLWE/MLWE Cryptanalysis": [
        "src/datasets",
        "src/attacks",
        "src/baselines",
        "experiments/toy_lwe",
        "experiments/rlwe_mlwe",
        "experiments/hybrid_attack",
        "configs/attack",
        "results/curves",
    ],
    "BKZ / Lattice Reduction": [
        "src/reduction",
        "src/estimators",
        "src/g6k_bridge",
        "src/fplll_bridge",
        "experiments/block_size_sweep",
        "experiments/gsa_deviation",
        "experiments/pruning",
        "configs/reduction",
    ],
    "ML-KEM / ML-DSA Implementation Security": [
        "src/audit",
        "src/ct_checks",
        "src/test_vectors",
        "experiments/timing",
        "experiments/fault",
        "experiments/leakage",
        "configs/audit",
    ],
    "ZK-friendly PQ Privacy": [
        "src/commitments",
        "src/encodings",
        "src/protocols",
        "src/params",
        "experiments/constraint_cost",
        "experiments/prototype",
        "configs/prototype",
    ],
}


TRACK_FILES = {
    "Module-SIS Primitive": {
        "paper/security_analysis.md": "# Security Analysis\n\nTODO_VERIFY：定义 correctness、collision resistance、binding/equivocation 和参数假设。\n",
        "paper/related_work.md": "# Related Work\n\nTODO_VERIFY：补 lattice commitments、Module-SIS primitives 和 chameleon hashes。\n",
        "configs/params/module_sis_toy.yaml": "security_level: toy\nmodule_rank: TODO_VERIFY\nmodulus: TODO_VERIFY\nnorm_bound: TODO_VERIFY\n",
        "configs/benchmark/default.yaml": "runs: 3\nmeasure: [correctness, runtime, size]\n",
    },
    "AI4Lattice": {
        "paper/limitations.md": "# Limitations\n\nTODO_VERIFY：区分 toy phenomenon、leakage artifact 与可迁移 attack subroutine。\n",
        "configs/model/toy_transformer.yaml": "model: toy_transformer\nrole: coordinate_selection\nseed: 0\n",
        "configs/attack/toy_lwe.yaml": "instance: toy_lwe\nn: TODO_VERIFY\nq: TODO_VERIFY\nsamples: TODO_VERIFY\n",
        "configs/attack/rlwe_mlwe.yaml": "instance: rlwe_mlwe_toy\nring_dim: TODO_VERIFY\nmodule_rank: TODO_VERIFY\n",
    },
    "LWE/RLWE/MLWE Cryptanalysis": {
        "paper/limitations.md": "# Limitations\n\nTODO_VERIFY：不能把 toy LWE 现象直接推广到真实参数。\n",
        "configs/attack/toy_lwe.yaml": "instance: toy_lwe\nn: TODO_VERIFY\nq: TODO_VERIFY\nsamples: TODO_VERIFY\n",
        "configs/attack/rlwe_mlwe.yaml": "instance: rlwe_mlwe_toy\nring_dim: TODO_VERIFY\nmodule_rank: TODO_VERIFY\n",
    },
    "BKZ / Lattice Reduction": {
        "paper/cost_model.md": "# Cost Model\n\nTODO_VERIFY：记录 BKZ/fplll/G6K/estimator 假设和适用边界。\n",
        "configs/reduction/bkz_sweep.yaml": "block_sizes: [TODO_VERIFY]\nstrategy: baseline\nestimator: TODO_VERIFY\n",
    },
    "ML-KEM / ML-DSA Implementation Security": {
        "docs/audit_checklist.md": "# Audit Checklist\n\n- [ ] constant-time\n- [ ] side-channel model\n- [ ] fault model\n- [ ] test vectors\n",
        "configs/audit/default.yaml": "target: TODO_VERIFY\nchecks: [constant_time, timing, fault, leakage]\n",
    },
    "ZK-friendly PQ Privacy": {
        "docs/privacy_model.md": "# Privacy Model\n\nTODO_VERIFY：定义 anonymity、linkability、credential 或 authentication 安全目标。\n",
        "docs/long_term_research_path.md": "# Long-term Research Path\n\n连接 lattice commitments、ZK-friendly encodings、PQ anonymous credentials 和 post-quantum identity systems。\n",
        "configs/prototype/default.yaml": "primitive: TODO_VERIFY\nproof_system: TODO_VERIFY\nconstraint_metric: TODO_VERIFY\n",
    },
}


def clean_text(value: object) -> str:
    text = sanitize(value)
    for marker in POLLUTION_MARKERS:
        text = text.replace(marker, "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [clean_text(item) for item in value if clean_text(item)]
    if isinstance(value, str) and value.strip():
        return [clean_text(value)]
    return []


def _load_json_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"paper plan JSON must contain an object: {path}")
    return payload


def _parse_markdown_plan(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s*Paper Plan:\s*(.+)$", text, flags=re.MULTILINE)
    track_match = re.search(r"Track[：:]\s*(.+)$", text, flags=re.MULTILINE)
    score_match = re.search(r"Score[：:]\s*(\d+)", text, flags=re.MULTILINE)
    return {
        "plan_id": "plan-" + short_hash(str(path)),
        "title": clean_text(title_match.group(1) if title_match else path.stem),
        "track": clean_text(track_match.group(1) if track_match else "Other"),
        "paper_plan_score": int(score_match.group(1)) if score_match else 0,
        "core_research_question": "TODO_VERIFY：Markdown 输入缺少结构化字段，需要人工核对。",
        "why_this_is_not_trivial": "TODO_VERIFY：从 Markdown 计划中补充。",
        "why_this_is_not_blind_combination": "TODO_VERIFY：从 Markdown 计划中补充。",
        "minimum_viable_paper": "TODO_VERIFY：从 Markdown 计划中补充。",
        "expected_contributions": {},
        "experiment_plan": [],
        "proof_or_security_analysis_plan": [],
        "source_papers": [],
        "advisor_questions": [],
        "risks": [],
        "next_7_days": [],
        "three_month_execution_plan": {},
        "warnings": ["Markdown 输入只做最小解析，必须人工核验。"],
    }


def load_plan(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        return _load_json_plan(path)
    if path.suffix.lower() in {".md", ".markdown"}:
        return _parse_markdown_plan(path)
    raise ValueError(f"unsupported paper plan format: {path}")


def resolve_plan_path(plan: Path, plan_id: str | None = None) -> Path:
    if plan.is_file():
        return plan
    if not plan.is_dir():
        raise FileNotFoundError(f"paper plan not found: {plan}")
    candidates = sorted(plan.glob("*.json"))
    if plan_id:
        for candidate in candidates:
            payload = _load_json_plan(candidate)
            if clean_text(payload.get("plan_id")) == plan_id:
                return candidate
        raise FileNotFoundError(f"plan_id {plan_id} not found under {plan}")
    if not candidates:
        raise FileNotFoundError(f"no paper plan JSON files under {plan}")
    return candidates[0]


def artifact_slug(plan: dict[str, Any], override: str | None = None) -> str:
    if override:
        return safe_slug(override, max_length=100)
    title = clean_text(plan.get("title") or plan.get("tentative_paper_title") or plan.get("plan_id") or "research-artifact")
    track = clean_text(plan.get("track") or "artifact")
    return safe_slug(f"{track}-{title}", max_length=100)


def directories_for_track(track: str) -> list[str]:
    dirs = list(BASE_DIRS)
    dirs.extend(TRACK_DIRS.get(track, []))
    return list(dict.fromkeys(dirs))


def files_for_track(track: str) -> dict[str, str]:
    return dict(TRACK_FILES.get(track, {}))


def _bullets(items: object, empty: str = "TODO_VERIFY") -> str:
    values = _as_list(items)
    if not values:
        values = [empty]
    return "\n".join(f"- {value}" for value in values)


def _dict_bullets(items: object) -> str:
    if not isinstance(items, dict) or not items:
        return "- TODO_VERIFY"
    return "\n".join(f"- {clean_text(key)}：{clean_text(value)}" for key, value in items.items())


def _source_papers(plan: dict[str, Any]) -> str:
    papers = plan.get("source_papers")
    if not isinstance(papers, list) or not papers:
        return "- TODO_VERIFY：Paper Plan 未提供 source_papers，不能编造 related work。"
    lines = []
    for paper in papers:
        if not isinstance(paper, dict):
            continue
        title = clean_text(paper.get("title")) or "unknown"
        url = clean_text(paper.get("url"))
        lines.append(f"- [{title}]({url})" if url else f"- {title}")
    return "\n".join(lines) if lines else "- TODO_VERIFY"


def render_readme(plan: dict[str, Any]) -> str:
    title = clean_text(plan.get("title")) or "Research Artifact"
    return f"""# {title}

## 1. Project title

{title}

## 2. Research question

{clean_text(plan.get("core_research_question")) or "TODO_VERIFY：需要人工确认研究问题。"}

## 3. Why this matters

{clean_text(plan.get("why_this_is_not_trivial")) or "TODO_VERIFY：需要说明为什么该问题对格密码/PQC/AI4Lattice 有意义。"}

## 4. Minimum viable paper

{clean_text(plan.get("minimum_viable_paper")) or "TODO_VERIFY：需要定义 3-6 个月内可完成的 MVP。"}

## 5. Expected contributions

{_dict_bullets(plan.get("expected_contributions"))}

## 6. Technical plan

- 非平庸性边界：{clean_text(plan.get("why_this_is_not_blind_combination")) or "TODO_VERIFY"}
- 技术路线必须从最小可验证对象开始。
- 尚无实验结果；所有结果都需要后续运行验证。

## 7. Experiment plan

{_bullets(plan.get("experiment_plan"))}

## 8. Security/proof analysis plan

{_bullets(plan.get("proof_or_security_analysis_plan"), "TODO_VERIFY：需要定义安全目标、攻击模型和证明入口。")}

## 9. Reproducibility plan

- 固定参数、随机种子、配置文件和运行命令。
- 保存环境说明、日志和失败样例。
- 尚无安全证明；任何安全结论必须等证明或参数分析完成后再写。

## 10. 3-month roadmap

{_roadmap(plan)}

## 11. Current status

- Status：scaffold created
- Results：TODO_VERIFY，尚无实验结果。
- Proof：TODO_VERIFY，尚无安全证明。
- Fallback：如果主贡献不成立，降级为 benchmark / artifact / workshop / negative result。
- 风险：实验可能不显著，安全分析可能过难，工程成本可能高于预期。

## 12. Next 7 days

{_bullets(plan.get("next_7_days"), "TODO_VERIFY：核对来源论文，写 MVP spec，列 baseline。")}
"""


def _roadmap(plan: dict[str, Any]) -> str:
    roadmap = plan.get("three_month_execution_plan")
    if not isinstance(roadmap, dict) or not roadmap:
        return "- TODO_VERIFY：补 Week 1-2、Week 3-4、Month 2、Month 3 计划。"
    lines: list[str] = []
    for phase, tasks in roadmap.items():
        lines.append(f"### {clean_text(phase)}")
        lines.append(_bullets(tasks))
    return "\n\n".join(lines)


def render_todo(plan: dict[str, Any]) -> str:
    return f"""# TODO

## Today

{_bullets(plan.get("next_7_days"), "打开来源论文并核对计划字段。")}

## This Week

- 写 MVP spec。
- 列 baseline、参数和失败判据。
- 准备一次 5 分钟组会口头说明。

## Month 1

- 完成最小 prototype。
- 跑第一轮 baseline。
- 记录失败样例。

## Month 2

- 扩展参数或实验矩阵。
- 补 related work 表格。
- 整理可复现实验脚本。

## Month 3

- 写 short paper / workshop draft。
- 完成 artifact README。
- 和导师确认投稿或降级方案。

## Advisor Discussion

{_bullets(plan.get("advisor_questions"), "TODO_VERIFY：请导师判断该计划是否值得推进。")}

## Risks to Verify

{_bullets(plan.get("risks"), "TODO_VERIFY：列出证明、实验、工程和投稿风险。")}

## Reading List

{_source_papers(plan)}
"""


def render_project_brief(plan: dict[str, Any]) -> str:
    questions = _as_list(plan.get("advisor_questions"))[:5] or ["TODO_VERIFY：这个方向是否值得投入 3-6 个月？"]
    return f"""# Project Brief

## 1. 一句话问题

{clean_text(plan.get("core_research_question")) or "TODO_VERIFY"}

## 2. 为什么不是平庸拼接

{clean_text(plan.get("why_this_is_not_blind_combination")) or "TODO_VERIFY"}

## 3. 最小实验 / 构造

{clean_text(plan.get("minimum_viable_paper")) or "TODO_VERIFY"}

## 4. 当前风险

{_bullets(plan.get("risks"), "TODO_VERIFY：需要确认 novelty、实验显著性和安全边界。")}

## 5. 需要导师拍板的问题

{_bullets(questions)}
"""


def render_outline(plan: dict[str, Any]) -> str:
    track = clean_text(plan.get("track"))
    method = "Construction / Method"
    if track in {"AI4Lattice", "BKZ / Lattice Reduction", "LWE/RLWE/MLWE Cryptanalysis"}:
        method = "Method / Experiment Setup"
    if track == "ML-KEM / ML-DSA Implementation Security":
        method = "Audit Method / Experiment Setup"
    return f"""# Paper Outline

## 1. Introduction

TODO_VERIFY：动机、问题和贡献边界。

## 2. Background

TODO_VERIFY：补格密码/PQC/attack/primitive 背景。

## 3. Related Work

{_source_papers(plan)}

## 4. {method}

{clean_text(plan.get("minimum_viable_paper")) or "TODO_VERIFY"}

## 5. Security Analysis / Attack Model / Experiment Setup

{_bullets(plan.get("proof_or_security_analysis_plan"), "TODO_VERIFY：定义安全目标、攻击模型或实验设置。")}

## 6. Evaluation

{_bullets(plan.get("evaluation_metrics"), "TODO_VERIFY：定义评价指标。")}

## 7. Limitations

- 尚无实验结果，不能写结论。
- 尚无安全证明，不能写安全声明。
- 必须区分 toy regime 和真实参数。

## 8. Conclusion

TODO_VERIFY：等实验和分析完成后再写。
"""


def _clean_markdown(text: str) -> str:
    for marker in POLLUTION_MARKERS:
        text = text.replace(marker, "")
    text = re.sub(r"<[^>]+>", "", text)
    return text.rstrip() + "\n"


def base_files(plan: dict[str, Any]) -> dict[str, str]:
    return {
        "README.md": render_readme(plan),
        "TODO.md": render_todo(plan),
        "PROJECT_BRIEF.md": render_project_brief(plan),
        "paper/outline.md": render_outline(plan),
        "docs/reproducibility.md": "# Reproducibility\n\nTODO_VERIFY：记录环境、参数、命令、随机种子、日志和失败样例。\n",
        "notes/reading_notes.md": "# Reading Notes\n\nTODO_VERIFY：阅读来源论文后补充。\n",
        "scripts/run_experiment.ps1": "Write-Host \"TODO_VERIFY: add reproducible experiment command\"\n",
        "tests/test_placeholder.py": "def test_scaffold_placeholder():\n    assert True\n",
    }


def build_manifest(plan: dict[str, Any], slug: str) -> tuple[list[str], dict[str, str]]:
    track = clean_text(plan.get("track"))
    dirs = directories_for_track(track)
    files = base_files(plan)
    files.update(files_for_track(track))
    files["artifact_manifest.json"] = json.dumps(
        {
            "slug": slug,
            "plan_id": clean_text(plan.get("plan_id")),
            "title": clean_text(plan.get("title")),
            "track": track,
            "created_from": "paper_plan",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "warning": "Scaffold only. No experimental result or security proof is included.",
        },
        ensure_ascii=False,
        indent=2,
    )
    return dirs, {path: _clean_markdown(content) if path.endswith((".md", ".ps1", ".py", ".yaml")) else content for path, content in files.items()}


def _backup_existing(target: Path, output_dir: Path) -> Path:
    backup_root = output_dir / "_backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backup_root / f"{target.name}__backup-{timestamp}"
    shutil.copytree(target, backup)
    shutil.rmtree(target)
    return backup


def create_artifact_scaffold(
    plan_path: Path,
    output_dir: Path = Path("research_artifacts"),
    *,
    force: bool = False,
    dry_run: bool = False,
    track_override: str | None = None,
    slug_override: str | None = None,
    plan_id: str | None = None,
) -> ArtifactResult:
    resolved = resolve_plan_path(plan_path, plan_id)
    plan = load_plan(resolved)
    if track_override:
        plan["track"] = track_override
    slug = artifact_slug(plan, slug_override)
    target = output_dir / slug
    dirs, files = build_manifest(plan, slug)
    directories = [target / item for item in dirs]
    file_paths = [target / item for item in files]
    backup_dir: Path | None = None
    if dry_run:
        return ArtifactResult(target, file_paths, directories, dry_run=True)
    if target.exists():
        if not force:
            raise FileExistsError(f"artifact already exists: {target}. Use --force to back it up and recreate.")
        backup_dir = _backup_existing(target, output_dir)
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    for rel_path, content in files.items():
        path = target / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return ArtifactResult(target, file_paths, directories, backup_dir=backup_dir)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a research artifact scaffold from a Paper Plan.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("research_artifacts"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--track-override", default=None)
    parser.add_argument("--slug", default=None)
    parser.add_argument("--plan-id", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = create_artifact_scaffold(
            args.plan,
            args.output_dir,
            force=args.force,
            dry_run=args.dry_run,
            track_override=args.track_override,
            slug_override=args.slug,
            plan_id=args.plan_id,
        )
    except Exception as exc:  # pragma: no cover - CLI safety path
        print(f"artifact scaffold failed: {exc}")
        return 1
    prefix = "DRY RUN: would create" if args.dry_run else "created"
    print(f"{prefix} artifact scaffold: {result.artifact_dir}")
    print(f"directories: {len(result.directories)}")
    print(f"files: {len(result.files)}")
    for path in result.files[:20]:
        print(path)
    if result.backup_dir:
        print(f"backup: {result.backup_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
