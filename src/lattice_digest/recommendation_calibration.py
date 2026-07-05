from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from lattice_digest.models import PaperRecord


TODO_VERIFY = "TODO_VERIFY"


@dataclass(frozen=True)
class RecommendationCalibration:
    recommendation_level: str
    recommendation_score: int
    recommendation_reason: str
    lattice_crypto_relevance: str
    user_relevance_tags: list[str]
    phd_application_relevance: str
    recommendation_risk_flags: list[str]
    recommendation_evidence_basis: list[str]
    recommendation_score_breakdown: dict[str, int]
    research_value_score: int
    primary_action_allowed: bool
    reading_priority: str
    suggested_action: str


@dataclass(frozen=True)
class RelevanceAxis:
    tag: str
    dimension: str
    contribution: int
    terms: tuple[str, ...]
    reason: str


AXES: tuple[RelevanceAxis, ...] = (
    RelevanceAxis("Sparse LWE/RLWE/MLWE", "cryptanalysis_relevance", 20, ("sparse lwe", "sparse rlwe", "sparse mlwe"), "directly targets sparse LWE/RLWE/MLWE cryptanalysis"),
    RelevanceAxis("LWE/RLWE/MLWE", "lattice_core_relevance", 24, ("lwe", "learning with errors", "rlwe", "ring-lwe", "mlwe", "module-lwe"), "matches the user's LWE/RLWE/MLWE core"),
    RelevanceAxis("SIS/Module-SIS", "lattice_core_relevance", 26, ("module-sis", "msis", "sis", "ring-sis"), "supports SIS/Module-SIS primitives and assumptions"),
    RelevanceAxis("ML-KEM/Kyber", "pqc_standard_relevance", 12, ("ml-kem", "kyber", "crystals-kyber"), "connects to ML-KEM/Kyber standardization or security"),
    RelevanceAxis("ML-DSA/Dilithium", "pqc_standard_relevance", 12, ("ml-dsa", "dilithium", "crystals-dilithium"), "connects to ML-DSA/Dilithium signatures"),
    RelevanceAxis("FN-DSA/Falcon", "pqc_standard_relevance", 10, ("fn-dsa", "falcon"), "connects to FN-DSA/Falcon signatures"),
    RelevanceAxis("HAWK", "pqc_standard_relevance", 8, ("hawk",), "tracks HAWK signature relevance"),
    RelevanceAxis("Lattice signatures", "lattice_core_relevance", 16, ("lattice signature", "lattice-based signature", "signature", "signatures"), "supports lattice-based signature reading"),
    RelevanceAxis("Ring/linkable ring signatures", "ZK_PQ_relevance", 6, ("ring signature", "linkable ring signature", "anonymous authentication"), "matches privacy primitives and anonymous authentication"),
    RelevanceAxis("Chameleon hash/trapdoor primitives", "ZK_PQ_relevance", 6, ("chameleon hash", "programmable hash", "hash-and-sign", "trapdoor", "commitment", "commitments"), "supports chameleon hash, trapdoor and commitment ideas"),
    RelevanceAxis("Lattice cryptanalysis", "cryptanalysis_relevance", 18, ("cryptanalysis", "attack", "attacks", "primal attack", "dual attack", "hybrid attack"), "directly supports lattice cryptanalysis work"),
    RelevanceAxis("Lattice reduction/BKZ/G6K", "cryptanalysis_relevance", 18, ("bkz", "lll", "g6k", "fplll", "lattice reduction", "sieving", "enumeration"), "supports BKZ/G6K/fplll attack baselines"),
    RelevanceAxis("AI4LC", "AI4LC_relevance", 10, ("ai-assisted lattice cryptanalysis", "ai4lc", "neural lattice", "coordinate selection", "learned pruning", "transformer", "swin"), "matches AI-assisted lattice cryptanalysis"),
    RelevanceAxis("ZK-friendly PQ primitives", "ZK_PQ_relevance", 6, ("zero-knowledge", "zk", "zk-friendly", "post-quantum proof"), "connects ZK systems to post-quantum or lattice primitives"),
    RelevanceAxis("PQC implementation/security", "implementation_security_relevance", 10, ("implementation", "constant-time", "side-channel", "fault", "ntt", "masking", "hardware", "risc-v"), "supports PQC implementation and security engineering"),
    RelevanceAxis("FHE/lattice HE", "lattice_core_relevance", 10, ("fhe", "fully homomorphic", "ckks", "bfv", "bgv", "tfhe", "bootstrapping"), "adds lattice-based FHE background"),
)


def calibrate_recommendation(
    record: PaperRecord,
    *,
    freshness_bucket: str,
    primary_today_new_eligible: bool,
    selected_date_basis: str,
    todo_verify_flags: list[str] | None = None,
    venue_confidence: str = "low",
    venue_status: str = "unknown",
    ccf_rank: str = "unknown",
) -> RecommendationCalibration:
    text = _record_text(record)
    axes = _matched_axes(text)
    breakdown = _score_breakdown(record, axes, venue_confidence, ccf_rank)
    risk_flags = _risk_flags(
        record,
        freshness_bucket=freshness_bucket,
        selected_date_basis=selected_date_basis,
        todo_verify_flags=todo_verify_flags or [],
        venue_status=venue_status,
    )
    raw_research_value = sum(breakdown.values())
    research_value = _clamp(raw_research_value, 0, 100)
    primary_allowed = primary_today_new_eligible and freshness_bucket == "primary_today_new"
    public_score = _public_score(research_value, primary_allowed, freshness_bucket, risk_flags)
    if primary_allowed and _has_strong_axis(axes) and public_score >= 45 and not _has_hard_verify_flag(risk_flags):
        public_score = max(public_score, 85)
    elif primary_allowed and _has_medium_axis(axes) and not _has_hard_verify_flag(risk_flags):
        public_score = max(public_score, 65)
    level = _level(public_score, primary_allowed, freshness_bucket, risk_flags, axes)
    action = _suggested_action(level, primary_allowed, research_value, freshness_bucket)
    tags = [axis.tag for axis in axes]
    reason = _reason(level, tags, risk_flags, research_value, primary_allowed)
    return RecommendationCalibration(
        recommendation_level=level,
        recommendation_score=public_score,
        recommendation_reason=reason,
        lattice_crypto_relevance=_lattice_relevance(tags, reason),
        user_relevance_tags=tags,
        phd_application_relevance=_phd_relevance(tags, research_value),
        recommendation_risk_flags=sorted(set(risk_flags)),
        recommendation_evidence_basis=_evidence_basis(record, axes),
        recommendation_score_breakdown=breakdown,
        research_value_score=research_value,
        primary_action_allowed=primary_allowed and action == "Read today",
        reading_priority=_reading_priority(level),
        suggested_action=action,
    )


def _record_text(record: PaperRecord) -> str:
    parts: list[str] = [
        record.title,
        record.abstract,
        record.reason,
        record.venue or "",
        record.source,
        " ".join(record.taxonomy_tags),
        " ".join(record.keywords_matched),
        " ".join(record.categories),
    ]
    return " ".join(part for part in parts if part).lower()


def _matched_axes(text: str) -> list[RelevanceAxis]:
    axes: list[RelevanceAxis] = []
    has_crypto_context = any(
        _contains_term(text, term)
        for term in (
            "lattice",
            "lwe",
            "rlwe",
            "mlwe",
            "sis",
            "module-sis",
            "pqc",
            "post-quantum",
            "cryptanalysis",
            "kyber",
            "dilithium",
            "falcon",
            "hawk",
        )
    )
    for axis in AXES:
        if axis.tag == "AI4LC" and not has_crypto_context:
            continue
        if axis.tag == "Lattice signatures" and "signature" in text and not has_crypto_context:
            continue
        if any(_contains_term(text, term) for term in axis.terms):
            axes.append(axis)
    return axes


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])", text) is not None


def _score_breakdown(
    record: PaperRecord,
    axes: list[RelevanceAxis],
    venue_confidence: str,
    ccf_rank: str,
) -> dict[str, int]:
    breakdown = {
        "lattice_core_relevance": 0,
        "pqc_standard_relevance": 0,
        "cryptanalysis_relevance": 0,
        "implementation_security_relevance": 0,
        "AI4LC_relevance": 0,
        "ZK_PQ_relevance": 0,
        "venue_confidence": _venue_score(venue_confidence, ccf_rank),
        "source_health": _source_health_score(record.source_health),
        "evidence_completeness": _evidence_score(record),
        "PhD_application_value": 0,
        "blog_or_note_value": 0,
        "idea_generation_value": 0,
    }
    for axis in axes:
        breakdown[axis.dimension] = max(breakdown[axis.dimension], axis.contribution)
    if axes:
        breakdown["PhD_application_value"] = 10 if any(axis.dimension in {"cryptanalysis_relevance", "lattice_core_relevance", "AI4LC_relevance"} for axis in axes) else 5
        breakdown["blog_or_note_value"] = 5 if len(axes) >= 2 else 3
        breakdown["idea_generation_value"] = 8 if any(axis.tag in {"SIS/Module-SIS", "Chameleon hash/trapdoor primitives", "AI4LC", "Lattice reduction/BKZ/G6K"} for axis in axes) else 4
    if record.relevance_label == "D":
        breakdown["evidence_completeness"] -= 10
    return breakdown


def _venue_score(confidence: str, ccf_rank: str) -> int:
    if ccf_rank in {"A", "B"}:
        return 5
    if ccf_rank == "C":
        return 3
    if confidence == "high":
        return 3
    if confidence == "medium":
        return 1
    if confidence in {TODO_VERIFY, "low"}:
        return -2
    return 0


def _source_health_score(source_health: str) -> int:
    health = (source_health or "").lower()
    if health == "red":
        return -15
    if health == "yellow":
        return -5
    return 0


def _evidence_score(record: PaperRecord) -> int:
    score = 0
    if record.source_url:
        score += 2
    if record.abstract:
        score += 3
    if record.publication_date or record.update_date or record.announcement_date or record.first_seen_date:
        score += 3
    if not record.abstract:
        score -= 10
    if not record.source_url:
        score -= 10
    return score


def _risk_flags(
    record: PaperRecord,
    *,
    freshness_bucket: str,
    selected_date_basis: str,
    todo_verify_flags: list[str],
    venue_status: str,
) -> list[str]:
    flags = list(todo_verify_flags)
    if freshness_bucket != "primary_today_new":
        flags.append(f"non_primary:{freshness_bucket}")
    if selected_date_basis == TODO_VERIFY:
        flags.append("missing_date_basis")
    if not record.abstract:
        flags.append("abstract_todo_verify")
    if not record.source_health:
        flags.append("source_health_missing")
    elif record.source_health.lower() in {"yellow", "red"}:
        flags.append(f"source_health_{record.source_health.lower()}")
    if venue_status == TODO_VERIFY:
        flags.append("venue_todo_verify")
    if not _matched_axes(_record_text(record)):
        flags.append("no_concrete_user_axis")
    return flags


def _public_score(
    research_value: int,
    primary_allowed: bool,
    freshness_bucket: str,
    risk_flags: list[str],
) -> int:
    score = research_value
    if not primary_allowed:
        score = min(score, 79)
    if freshness_bucket == "date_uncertain_todo_verify":
        score = min(score, 39)
    if any(flag in risk_flags for flag in ("missing_date_basis", "source_health_red", "no_concrete_user_axis")):
        score = min(score, 59)
    if "source_health_yellow" in risk_flags:
        score = min(score, 84)
    return _clamp(score, 0, 100)


def _has_strong_axis(axes: list[RelevanceAxis]) -> bool:
    strong_tags = {
        "Sparse LWE/RLWE/MLWE",
        "LWE/RLWE/MLWE",
        "SIS/Module-SIS",
        "ML-KEM/Kyber",
        "ML-DSA/Dilithium",
        "FN-DSA/Falcon",
        "HAWK",
        "Lattice cryptanalysis",
        "Lattice reduction/BKZ/G6K",
        "AI4LC",
        "Chameleon hash/trapdoor primitives",
    }
    return any(axis.tag in strong_tags for axis in axes)


def _has_medium_axis(axes: list[RelevanceAxis]) -> bool:
    medium_tags = {
        "PQC implementation/security",
        "FHE/lattice HE",
        "ZK-friendly PQ primitives",
        "Lattice signatures",
        "Ring/linkable ring signatures",
    }
    return any(axis.tag in medium_tags for axis in axes)


def _has_hard_verify_flag(risk_flags: list[str]) -> bool:
    return any(flag in risk_flags for flag in ("missing_date_basis", "source_health_red", "no_concrete_user_axis"))


def _level(
    score: int,
    primary_allowed: bool,
    freshness_bucket: str,
    risk_flags: list[str],
    axes: list[RelevanceAxis],
) -> str:
    if any(flag in risk_flags for flag in ("missing_date_basis", "source_health_red", "no_concrete_user_axis")):
        return TODO_VERIFY
    if not primary_allowed:
        return "Backfill" if freshness_bucket != "date_uncertain_todo_verify" else TODO_VERIFY
    if not axes:
        return TODO_VERIFY
    if score >= 85:
        return "Strong"
    if score >= 65:
        return "Medium"
    if score > 0:
        return "Low"
    return TODO_VERIFY


def _suggested_action(level: str, primary_allowed: bool, research_value: int, freshness_bucket: str) -> str:
    if level == TODO_VERIFY:
        return "TODO_VERIFY before reading"
    if not primary_allowed:
        if freshness_bucket in {"official_status_changed", "high_priority_security_update"}:
            return "Skim official update; keep outside primary-new"
        if research_value >= 75:
            return "Save for background"
        return "Skim for related work"
    if level == "Strong":
        return "Read today"
    if level == "Medium":
        return "Read this week"
    if level == "Low":
        return "Skim for related work"
    return "Save for background"


def _reading_priority(level: str) -> str:
    return {
        "Strong": "必须精读",
        "Medium": "建议精读",
        "Low": "可略读",
        "Backfill": "暂存",
        TODO_VERIFY: "低相关",
    }.get(level, "低相关")


def _reason(
    level: str,
    tags: list[str],
    risk_flags: list[str],
    research_value: int,
    primary_allowed: bool,
) -> str:
    if not tags:
        return "TODO_VERIFY: insufficient concrete user relevance axis; verify before using as recommendation."
    axis_text = "; ".join(tags[:4])
    prefix = f"{level}: {axis_text}"
    if level == "Backfill":
        return f"{prefix}; research value {research_value}/100, but freshness routes it outside primary today/new."
    if not primary_allowed and level != TODO_VERIFY:
        return f"{prefix}; useful for research, but not eligible for primary today/new."
    if risk_flags:
        return f"{prefix}; risk flags: {', '.join(sorted(set(risk_flags))[:3])}."
    return f"{prefix}; recommended because it matches concrete lattice/PQC research axes."


def _lattice_relevance(tags: list[str], fallback: str) -> str:
    if tags:
        return "Concrete user relevance axes: " + "; ".join(tags)
    return fallback


def _phd_relevance(tags: list[str], research_value: int) -> str:
    if not tags:
        return "TODO_VERIFY: no concrete PhD/application relevance axis detected."
    if research_value >= 75:
        return "High: useful for PhD reading, PI email, blog note, or project idea triage."
    if research_value >= 50:
        return "Medium: useful as related work or background for research planning."
    return "Low: keep only if later work links it to the main research direction."


def _evidence_basis(record: PaperRecord, axes: list[RelevanceAxis]) -> list[str]:
    basis = ["title"]
    if record.abstract:
        basis.append("abstract")
    if record.reason:
        basis.append("classifier_reason")
    if record.taxonomy_tags:
        basis.append("taxonomy_tags")
    if record.keywords_matched:
        basis.append("keywords")
    if record.source_url:
        basis.append("source_url")
    if axes:
        basis.append("deterministic_user_axis_match")
    return basis


def _clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, int(value)))


def calibration_to_update(calibration: RecommendationCalibration) -> dict[str, Any]:
    return {
        "recommendation_level": calibration.recommendation_level,
        "recommendation_score": calibration.recommendation_score,
        "recommendation_reason": calibration.recommendation_reason,
        "lattice_crypto_relevance": calibration.lattice_crypto_relevance,
        "user_relevance_tags": calibration.user_relevance_tags,
        "phd_application_relevance": calibration.phd_application_relevance,
        "recommendation_risk_flags": calibration.recommendation_risk_flags,
        "recommendation_evidence_basis": calibration.recommendation_evidence_basis,
        "recommendation_score_breakdown": calibration.recommendation_score_breakdown,
        "research_value_score": calibration.research_value_score,
        "primary_action_allowed": calibration.primary_action_allowed,
        "suggested_action": calibration.suggested_action,
    }


def has_calibrated_recommendation(record: PaperRecord | Mapping[str, Any]) -> bool:
    if isinstance(record, Mapping):
        return bool(record.get("recommendation_score_breakdown") or record.get("user_relevance_tags"))
    return bool(record.recommendation_score_breakdown or record.user_relevance_tags)
