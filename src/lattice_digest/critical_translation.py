from __future__ import annotations

import re
from dataclasses import dataclass

from lattice_digest.critical_security import CRITICAL
from lattice_digest.models import PaperRecord


TODO_VERIFY_TRANSLATION = "TODO_VERIFY_TRANSLATION"

TERMINOLOGY_LOCKS: tuple[tuple[str, str], ...] = (
    ("Dihedral Coset Problem", "二面体陪集问题"),
    ("Dihedral Subgroup Problem", "二面体子群问题"),
    ("Hidden Subgroup Problem", "隐藏子群问题"),
    ("polynomial-time quantum algorithm", "多项式时间量子算法"),
    ("approximation factor", "近似因子"),
    ("faulty sample rate", "错误样本率"),
    ("Preliminary Draft", "初步草稿"),
)

FORBIDDEN_ESCALATIONS: tuple[str, ...] = (
    "ML-KEM 已被攻破",
    "ML-DSA 已被攻破",
    "Module-LWE 已有多项式时间破解算法",
    "NIST PQC 标准已经失效",
)


@dataclass(frozen=True)
class TranslationCheck:
    status: str
    missing: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()


def _source_text(record: PaperRecord) -> str:
    return " ".join(part for part in (record.title, record.abstract, record.conclusion, record.venue or "") if part)


def source_math_fragments(text: str) -> list[str]:
    """Keep complete source math spans and balanced plain-text complexity terms.

    Never scan across a closed formula into an unrelated English sentence.
    Unclosed delimiters are left to the separately preserved source abstract.
    """
    spans = [(m.start(), m.end(), m.group()) for m in re.finditer(
        r"(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$|(?<!\\)\$(?!\$)[^$\n]*?(?<!\\)\$|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]", text)]
    for match in re.finditer(r"(?:\d+/)?O\(", text):
        if any(a <= match.start() < b for a, b, _ in spans):
            continue
        if len(re.findall(r"(?<!\\)\$", text[:match.start()])) % 2:
            # Do not reinterpret an unterminated source math span as plain text.
            continue
        depth = 1
        pos = match.end()
        while pos < len(text) and depth and text[pos] not in ";.\n$":
            depth += (text[pos] == "(") - (text[pos] == ")")
            pos += 1
        if depth == 0:
            spans.append((match.start(), pos, text[match.start():pos]))
    return list(dict.fromkeys(value for _, _, value in sorted(spans)))


def _protected_tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"\b(?:DCP|DHSP|EDCP|LWE|RLWE|MLWE|SVP|SIS|ML-KEM|ML-DSA|Module-LWE)\b", text))
    tokens.update(source_math_fragments(text))
    tokens.update(re.findall(r"\b\d+(?:\.\d+)?(?:%|/[A-Za-z]+)?\b", text))
    return tokens


def validate_critical_translation(source_text: str, chinese_text: str) -> TranslationCheck:
    missing: list[str] = []
    for english, chinese in TERMINOLOGY_LOCKS:
        if english.lower() in source_text.lower() and chinese not in chinese_text:
            missing.append(f"term:{english}")
    for token in sorted(_protected_tokens(source_text)):
        if token not in chinese_text:
            missing.append(f"token:{token}")
    source_lower = source_text.lower()
    if re.search(r"\b(?:preliminary|draft)\b", source_lower) and not any(term in chinese_text for term in ("初步", "草稿")):
        missing.append("qualifier:preliminary")
    if re.search(r"\b(?:claim|claims|claimed)\b", source_lower) and "声称" not in chinese_text:
        missing.append("qualifier:claimed")
    if re.search(r"\b(?:can|may|could)\b", source_lower) and not any(term in chinese_text for term in ("可能", "可", "或许")):
        missing.append("qualifier:modal")
    if re.search(r"\b(?:not|no|does not|cannot)\b", source_lower) and not any(term in chinese_text for term in ("不", "未", "无")):
        missing.append("negation")
    forbidden = [phrase for phrase in FORBIDDEN_ESCALATIONS if phrase in chinese_text]
    return TranslationCheck(
        status="VERIFIED_TERM_LOCKS" if not missing and not forbidden else TODO_VERIFY_TRANSLATION,
        missing=tuple(missing),
        forbidden=tuple(forbidden),
    )


def build_critical_claim_translation(record: PaperRecord) -> str:
    source = _source_text(record)
    lower = source.lower()
    parts: list[str] = []
    if "preliminary" in lower or "draft" in lower:
        parts.append("该初步草稿")
    else:
        parts.append("该论文")
    claim_verb = "声称" if re.search(r"\b(?:claim|claims|claimed)\b", lower) else "报告"
    if "dihedral coset problem" in lower and "polynomial-time quantum algorithm" in lower:
        parts.append(f"{claim_verb}提出针对二面体陪集问题（DCP）的多项式时间量子算法")
    else:
        parts.append(f"{claim_verb}提出潜在的关键格密码安全结果")
    if "regev" in lower and "reduction" in lower:
        parts.append("并声称结合 Regev 从格问题到 DCP 的归约及后续改进归约")
    if "approximation factor" in lower:
        parts.append("并保留原文所述近似因子")
    targets = [target for target in ("approximate SVP", "SVP", "LWE", "RLWE", "MLWE", "SIS", "Module-SIS") if target.lower() in lower]
    if targets:
        rendered = "、".join(dict.fromkeys(targets))
        parts.append(f"可对 {rendered} 产生潜在的多项式时间量子算法后果")
    # Parameter expressions stay verbatim and separate from translated prose.
    # This preserves alpha and nested parentheses without inventing a mapping
    # from asymptotic LWE to a standardized ML-KEM parameter set.
    formulas = source_math_fragments(source)
    if "faulty sample" in lower:
        parts.append("并声称可容忍原文给出的错误样本率")
    if formulas:
        parts.append("原文数学表达逐项保留：" + "；".join(formulas))
    text = "，".join(parts) + "。"
    text += "该结果仍为 TODO_VERIFY；目前不能据此断言 ML-KEM、ML-DSA 或标准化 Module-LWE 的安全性已经失效。"
    if "https://eprint.iacr.org/2026/1693" in record.abstract:
        text += ("公开争议：原摘要明确关联反驳论文 https://eprint.iacr.org/2026/1693；"
                 "原主张与反驳均须对照全文，未独立复核数学证明，未执行 Lean。")
    if re.search(r"does not solve|cannot succeed|no-go", source, re.I):
        # A negative result must never inherit the positive algorithm template.
        text = ("作者反驳：该论文报告针对 DCP 算法的否定性分析；"
                "这属于作者报告的研究结论，尚未独立复核全文证明或执行 Lean。"
                "不应据此声称标准化 ML-KEM 或 ML-DSA 已被攻破。")
        if formulas:
            text += "原文数学表达逐项保留：" + "；".join(formulas) + "。"
    return text


def apply_critical_translation(record: PaperRecord) -> PaperRecord:
    if record.security_impact_severity != CRITICAL:
        return record
    source = _source_text(record)
    translation = build_critical_claim_translation(record)
    check = validate_critical_translation(source, translation)
    flags = list(record.translation_fidelity_flags)
    flags.extend(check.missing)
    flags.extend(f"forbidden:{item}" for item in check.forbidden)
    overall_status = check.status
    if record.translation_fidelity_status == TODO_VERIFY_TRANSLATION:
        overall_status = TODO_VERIFY_TRANSLATION
    if overall_status == TODO_VERIFY_TRANSLATION:
        flags.append(TODO_VERIFY_TRANSLATION)
    return record.model_copy(
        update={
            "critical_claim_zh": translation,
            "translation_fidelity_status": overall_status,
            "translation_fidelity_flags": sorted(set(flags)),
        }
    )
