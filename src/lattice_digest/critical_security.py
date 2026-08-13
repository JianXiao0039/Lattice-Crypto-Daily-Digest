from __future__ import annotations

import re
from dataclasses import dataclass

from lattice_digest.models import PaperRecord


CRITICAL = "CRITICAL"
UNKNOWN = "UNKNOWN"
READ_AND_VERIFY_IMMEDIATELY = "READ_AND_VERIFY_IMMEDIATELY"


@dataclass(frozen=True)
class CriticalSecurityAnalysis:
    severity: str = UNKNOWN
    confidence: str = "TODO_VERIFY"
    document_maturity: str = "unknown"
    source_evidence_terms: tuple[str, ...] = ()
    relations: tuple[dict[str, str], ...] = ()
    targets: tuple[str, ...] = ()
    qualifiers: tuple[str, ...] = ()
    explanation: str = ""

    @property
    def is_critical(self) -> bool:
        return self.severity == CRITICAL


_TARGET_PATTERNS: tuple[tuple[str, str], ...] = (
    ("MLWE", r"\b(?:mlwe|module[- ]lwe|module learning with errors)\b"),
    ("RLWE", r"\b(?:rlwe|ring[- ]lwe|ring learning with errors)\b"),
    ("LWE", r"\b(?:lwe|learning with errors)\b"),
    ("Module-SIS", r"\b(?:module[- ]sis|msis)\b"),
    ("SIS", r"\b(?:sis|short integer solution)\b"),
    ("approximate SVP", r"\b(?:approx(?:imate|imation)?[- ]svp|approx(?:imate|imation)?[- ]factor[^.;]{0,50}svp)\b"),
    ("SVP", r"\b(?:svp|shortest vector problem)\b"),
    ("lattice problem", r"\blattice (?:problem|problems|hardness|assumption|assumptions)\b"),
)

_DCP_PATTERN = re.compile(
    r"\b(?:dcp|dihedral coset problem|dhsp|dihedral hidden subgroup problem|"
    r"edcp|extrapolated dihedral coset problem)\b",
    re.IGNORECASE,
)
_POLYNOMIAL_QUANTUM_PATTERN = re.compile(
    r"\b(?:polynomial[- ]time quantum algorithm|quantum algorithm[^.;]{0,90}polynomial[- ]time)\b",
    re.IGNORECASE,
)
_QUANTUM_PATTERN = re.compile(r"\bquantum algorithm\b", re.IGNORECASE)
_DCP_SOLVE_PATTERN = re.compile(
    r"(?:polynomial[- ]time quantum algorithm[^.;]{0,100}(?:for|solv(?:e|es|ing))[^.;]{0,40}"
    r"(?:dcp|dihedral coset problem)|(?:solve|solves|solving)[^.;]{0,60}"
    r"(?:dcp|dihedral coset problem)[^.;]{0,80}(?:quantum|polynomial))",
    re.IGNORECASE,
)
_VALID_REDUCTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?:regev(?:'s)?\s+)?reduction\s+of\s+(?:lattice problems?|lwe|learning with errors|"
        r"(?:approximate\s+)?svp|shortest vector problem)\s+to\s+(?:the\s+)?"
        r"(?:dcp|dihedral coset problem|edcp|extrapolated dihedral coset problem)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:lattice problems?|lwe|learning with errors|(?:approximate\s+)?svp|shortest vector problem)"
        r"[^.;]{0,80}\breduc(?:e|es|ed|tion)\b[^.;]{0,40}\b(?:dcp|dihedral coset problem|edcp|extrapolated dihedral coset problem)\b",
        re.IGNORECASE,
    ),
)
_DIRECT_CONSEQUENCE_PATTERN = re.compile(
    r"(?:yield|yields|give|gives|imply|implies|solve|solves|algorithm(?:s)?\s+for)"
    r"[^.;]{0,100}(?:lwe|learning with errors|(?:approximate\s+)?svp|shortest vector problem|lattice problems?)",
    re.IGNORECASE,
)
_CONSEQUENCE_PATTERN = re.compile(
    r"\b(?:solve|solves|yield|yields|attack|attacks|threaten|threatens|undermine|undermines|cryptanalysis)\b",
    re.IGNORECASE,
)
_QUALIFIERS: tuple[tuple[str, str], ...] = (
    ("preliminary", r"\bpreliminary\b"),
    ("draft", r"\bdraft\b"),
    ("claimed", r"\b(?:claim|claims|claimed)\b"),
    ("modal", r"\b(?:can|may|could)\b"),
    ("conditional", r"\b(?:conditional|assuming|provided that)\b"),
    ("sketch", r"\bsketch\b"),
)


def _source_text(record: PaperRecord) -> str:
    return " ".join(part for part in (record.title, record.abstract, record.conclusion) if part)


def _matched_targets(text: str) -> list[str]:
    targets: list[str] = []
    for name, pattern in _TARGET_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            targets.append(name)
    return targets


def _qualifiers(text: str, record: PaperRecord) -> list[str]:
    result = [name for name, pattern in _QUALIFIERS if re.search(pattern, text, re.IGNORECASE)]
    flags = " ".join(record.TODO_VERIFY_flags).lower()
    if "preliminary" in flags and "preliminary" not in result:
        result.append("preliminary")
    if record.venue and "preliminary draft" in record.venue.lower():
        for item in ("preliminary", "draft"):
            if item not in result:
                result.append(item)
    return result


def analyze_critical_security_signal(record: PaperRecord) -> CriticalSecurityAnalysis:
    text = _source_text(record)
    lower = text.lower()
    targets = _matched_targets(text)
    qualifiers = _qualifiers(text, record)
    has_dcp = bool(_DCP_PATTERN.search(text))
    polynomial_quantum = bool(_POLYNOMIAL_QUANTUM_PATTERN.search(text))
    quantum = polynomial_quantum or bool(_QUANTUM_PATTERN.search(text))
    solves_dcp = has_dcp and (bool(_DCP_SOLVE_PATTERN.search(text)) or (polynomial_quantum and "algorithm for" in lower))
    valid_reduction = next((match for pattern in _VALID_REDUCTION_PATTERNS if (match := pattern.search(text))), None)
    direct_consequence = bool(_DIRECT_CONSEQUENCE_PATTERN.search(text)) and bool(targets)
    consequence_language = bool(_CONSEQUENCE_PATTERN.search(text))

    relations: list[dict[str, str]] = []
    if solves_dcp:
        relations.append(
            {
                "relation": "SOLVES",
                "subject": "polynomial-time quantum algorithm" if polynomial_quantum else "quantum algorithm",
                "object": "DCP",
                "evidence_field": "source_content",
            }
        )
    if valid_reduction:
        relations.append(
            {
                "relation": "REDUCES_TO",
                "subject": "approximate SVP/LWE/lattice problem",
                "object": "DCP",
                "evidence_field": "source_content",
            }
        )
    if polynomial_quantum:
        relations.extend(
            [
                {
                    "relation": "ALGORITHM_COMPLEXITY",
                    "subject": "algorithm",
                    "object": "polynomial_time",
                    "evidence_field": "source_content",
                },
                {
                    "relation": "ALGORITHM_MODEL",
                    "subject": "algorithm",
                    "object": "quantum",
                    "evidence_field": "source_content",
                },
            ]
        )

    reduction_chain = polynomial_quantum and solves_dcp and valid_reduction is not None and bool(targets)
    explicit_direct_chain = polynomial_quantum and direct_consequence and consequence_language and bool(targets)
    critical = reduction_chain or explicit_direct_chain
    if critical:
        relations.append(
            {
                "relation": "CLAIMED_CONSEQUENCE",
                "subject": "polynomial-time quantum algorithm",
                "object": ", ".join(targets),
                "evidence_field": "source_content",
            }
        )

    evidence_terms: list[str] = []
    if has_dcp:
        evidence_terms.append("DCP")
    if polynomial_quantum:
        evidence_terms.append("polynomial-time quantum algorithm")
    elif quantum:
        evidence_terms.append("quantum algorithm")
    evidence_terms.extend(targets)
    if valid_reduction:
        evidence_terms.append("lattice-problem-to-DCP reduction")
    if "regev" in lower:
        evidence_terms.append("Regev reduction")
    if re.search(r"faulty sample(?:s| rate)?", text, re.IGNORECASE):
        evidence_terms.append("faulty sample rate")

    maturity = "preliminary_draft" if {"preliminary", "draft"} & set(qualifiers) else "unknown"
    explanation = (
        "Directionally supported DCP quantum-algorithm plus lattice-problem-to-DCP reduction chain; "
        "impact is critical if correct, while evidence remains TODO_VERIFY."
        if critical
        else "No complete critical lattice-security consequence chain was found in source-grounded content."
    )
    return CriticalSecurityAnalysis(
        severity=CRITICAL if critical else UNKNOWN,
        confidence="TODO_VERIFY",
        document_maturity=maturity,
        source_evidence_terms=tuple(dict.fromkeys(evidence_terms)),
        relations=tuple(relations),
        targets=tuple(dict.fromkeys(targets)),
        qualifiers=tuple(dict.fromkeys(qualifiers)),
        explanation=explanation,
    )


def apply_critical_security_analysis(record: PaperRecord) -> PaperRecord:
    analysis = analyze_critical_security_signal(record)
    flags = list(record.TODO_VERIFY_flags)
    if analysis.is_critical:
        flags.extend(
            [
                "critical_security_claim_todo_verify",
                "no_parameter_specific_standard_break_established",
            ]
        )
        if analysis.document_maturity == "preliminary_draft":
            flags.append("preliminary_draft")
    return record.model_copy(
        update={
            "security_impact_severity": analysis.severity,
            "evidence_confidence": analysis.confidence,
            "document_maturity": analysis.document_maturity,
            "critical_signal_relations": list(analysis.relations),
            "critical_signal_explanation": analysis.explanation,
            "source_evidence_terms": sorted(
                set(record.source_evidence_terms) | set(analysis.source_evidence_terms), key=str.lower
            ),
            "TODO_VERIFY_flags": sorted(set(flags)),
        }
    )
