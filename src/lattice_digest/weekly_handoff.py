from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from lattice_digest.report_quality import lattice_pqc_anchor_evidence, source_health_caveat_text


SCHEMA_VERSION = 1

TRACK_MODULE_SIS = "module_sis_chameleon_hash"
TRACK_XINGYE_BRIDGE = "xingye_lu_bridge"
TRACK_AI4LATTICE = "ai4lattice_longline"
TRACK_MLKEM_MLDSA = "mlkem_mldsa_background"
TRACK_PRIVACY = "privacy_registration_watchlist"
TRACK_EXCLUDED = "excluded_noise"

TRACK_ORDER = (
    TRACK_MODULE_SIS,
    TRACK_XINGYE_BRIDGE,
    TRACK_AI4LATTICE,
    TRACK_MLKEM_MLDSA,
    TRACK_PRIVACY,
    TRACK_EXCLUDED,
)

ACTION_HANDOFF_NOW = "handoff_now"
ACTION_HANDOFF_AFTER_VERIFY = "handoff_after_verify"
ACTION_KEEP_IN_RADAR = "keep_in_radar"
ACTION_BACKLOG = "backlog"
ACTION_EXCLUDE = "exclude"

ACTION_ORDER = (
    ACTION_HANDOFF_NOW,
    ACTION_HANDOFF_AFTER_VERIFY,
    ACTION_KEEP_IN_RADAR,
    ACTION_BACKLOG,
    ACTION_EXCLUDE,
)

NON_CLAIMS = [
    "this is not a security proof",
    "this is not a novelty claim",
    "this is not a claim that the construction works",
    "this is not a claim that a PI works on a topic",
    "this is not a publication claim",
    "this is a research triage and handoff record only",
]

SCORE_FIELDS = (
    "module_sis_relevance_score",
    "chameleon_hash_relevance_score",
    "xingye_bridge_relevance_score",
    "ai4lattice_relevance_score",
    "implementation_reproducibility_usefulness",
    "proof_usefulness",
    "parameterization_usefulness",
    "verification_burden",
    "overclaim_risk",
)

PACKET_FIELDS = (
    "handoff_id",
    "week_id",
    "source_record_id",
    "title",
    "authors_raw",
    "source",
    "url_or_identifier",
    "track",
    "action_label",
    "lattice_pqc_anchor_evidence",
    *SCORE_FIELDS,
    "intended_research_artifact_target",
    "todo_verify",
    "non_claims",
)

TOP_LEVEL_FIELDS = (
    "schema_version",
    "week_id",
    "source_weekly_json",
    "coverage",
    "source_health_summary",
    "source_health_caveat",
    "track_counts",
    "action_counts",
    "packets",
    "excluded",
    "todo_verify",
)

MODULE_SIS_TERMS = (
    "module-sis",
    "module sis",
    "msis",
    "short integer solution",
    "ring-sis",
    "ring sis",
)
SIS_TERMS = (*MODULE_SIS_TERMS, " sis ", "sis/", "/sis", "sis-based")
CHAMELEON_TERMS = ("chameleon hash", "chameleon hashing")
COMMITMENT_TERMS = ("lattice commitment", "lattice-based commitment", "sis commitment", "module-sis commitment")
TRAPDOOR_TERMS = ("lattice trapdoor", "trapdoor sampling", "trapdoor collision", "preimage sampling", "gadget matrix")
BRIDGE_TERMS = (
    "linkable ring signature",
    "lattice ring signature",
    "lattice-based ring signature",
    "blind lattice signature",
    "lattice-based blind signature",
    "hash-then-one-way",
    "programmable hash",
    "anonymous authentication",
)
AI_TERMS = (
    "ai-assisted",
    "machine learning",
    "deep learning",
    "neural",
    "transformer",
    "swin",
    "learned",
    "coordinate selection",
)
AI_LATTICE_TERMS = (
    "lattice cryptanalysis",
    "lattice reduction",
    "lwe",
    "rlwe",
    "mlwe",
    "module-lwe",
    "bkz",
    "primal attack",
    "dual attack",
    "hybrid attack",
    "sparse lwe",
)
MLKEM_MLDSA_TERMS = ("ml-kem", "kyber", "ml-dsa", "dilithium", "fips 203", "fips 204")
PRIVACY_TERMS = (
    "privacy",
    "registration",
    "ring signature",
    "anonymous",
    "credential",
    "zero-knowledge",
    " zk ",
    "secure aggregation",
    "commitment",
)
IMPLEMENTATION_TERMS = (
    "implementation",
    "reproducib",
    "benchmark",
    "constant-time",
    "side-channel",
    "fault",
    "hardware",
    "software",
    "audit",
    "parameter",
)
PROOF_TERMS = ("proof", "security model", "reduction", "theorem", "assumption", "collision resistance")
PARAMETER_TERMS = ("parameter", "norm bound", "modulus", "dimension", "estimator", "security estimate")
GENERIC_RISK_TERMS = (
    "hash",
    "commitment",
    "registration",
    "privacy",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "llm",
    "optimization",
    "blockchain",
    "zero-knowledge",
    " zk ",
    "ring signature",
)


def _stable_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value}, key=str.casefold)


def _record_text(record: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "title",
        "abstract",
        "reason",
        "reason_for_priority",
        "why_it_matters",
        "suggested_action",
        "source",
        "venue",
    ):
        value = record.get(key)
        if value:
            parts.append(str(value))
    for key in (
        "taxonomy_tags",
        "keywords_matched",
        "negative_keywords_matched",
        "research_tags",
        "tags",
    ):
        value = record.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value if item is not None)
    explanation = record.get("ranking_explanation")
    if isinstance(explanation, dict):
        matched = explanation.get("matched_taxonomy")
        if isinstance(matched, list):
            parts.extend(str(item) for item in matched)
    return f" {' '.join(parts).lower()} "


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _score(text: str, groups: tuple[tuple[str, ...], ...]) -> int:
    return min(5, sum(1 for terms in groups if _contains(text, terms)))


def _source_record_id(record: dict[str, Any]) -> str:
    for key in ("dedup_key", "paper_id", "doi", "arxiv_id", "eprint_id", "source_url", "url"):
        value = str(record.get(key) or "").strip()
        if value:
            return f"{key}:{value}"
    title = re.sub(r"[^a-z0-9]+", "-", str(record.get("title") or "untitled").lower()).strip("-")
    return f"title:{title or 'untitled'}"


def _packet_id(week_id: str, source_record_id: str, track: str) -> str:
    digest = hashlib.sha256(f"{week_id}|{source_record_id}|{track}".encode("utf-8")).hexdigest()[:12]
    return f"QPH-{week_id}-{digest}"


def _url_or_identifier(record: dict[str, Any]) -> str:
    for key in ("doi", "eprint_id", "arxiv_id", "source_url", "url"):
        value = str(record.get(key) or "").strip()
        if value:
            return value
    return ""


def _hard_anchors(record: dict[str, Any]) -> list[str]:
    evidence_record = dict(record)
    # Existing weekly sections are intentionally broad discovery buckets. They
    # are useful context, but must not become hard handoff evidence by themselves.
    evidence_record.pop("research_sections", None)
    evidence_record.pop("report_buckets", None)
    return _stable_unique(lattice_pqc_anchor_evidence(evidence_record))


def _classify_track(record: dict[str, Any]) -> str:
    text = _record_text(record)
    anchors = _hard_anchors(record)
    has_anchor = bool(anchors)
    direct_module = _contains(text, MODULE_SIS_TERMS) and _contains(
        text, (*CHAMELEON_TERMS, *COMMITMENT_TERMS, *TRAPDOOR_TERMS)
    )
    sis_adjacent = _contains(text, SIS_TERMS) and _contains(
        text, (*CHAMELEON_TERMS, *COMMITMENT_TERMS, *TRAPDOOR_TERMS)
    )
    if has_anchor and (direct_module or sis_adjacent or _contains(text, CHAMELEON_TERMS)):
        return TRACK_MODULE_SIS
    if has_anchor and _contains(text, BRIDGE_TERMS):
        return TRACK_XINGYE_BRIDGE
    if has_anchor and _contains(text, AI_TERMS) and _contains(text, AI_LATTICE_TERMS):
        return TRACK_AI4LATTICE
    if has_anchor and _contains(text, MLKEM_MLDSA_TERMS):
        return TRACK_MLKEM_MLDSA
    if has_anchor and _contains(text, PRIVACY_TERMS):
        return TRACK_PRIVACY
    return TRACK_EXCLUDED


def _scores(record: dict[str, Any], track: str) -> dict[str, int]:
    text = _record_text(record)
    module_score = _score(
        text,
        (
            MODULE_SIS_TERMS,
            SIS_TERMS,
            CHAMELEON_TERMS,
            COMMITMENT_TERMS,
            TRAPDOOR_TERMS,
        ),
    )
    chameleon_score = _score(text, (CHAMELEON_TERMS, COMMITMENT_TERMS, TRAPDOOR_TERMS))
    bridge_score = _score(text, (BRIDGE_TERMS, COMMITMENT_TERMS, CHAMELEON_TERMS))
    ai_score = _score(text, (AI_TERMS, AI_LATTICE_TERMS))
    implementation_score = _score(text, (IMPLEMENTATION_TERMS, PARAMETER_TERMS))
    proof_score = _score(text, (PROOF_TERMS, MODULE_SIS_TERMS, CHAMELEON_TERMS, TRAPDOOR_TERMS))
    parameter_score = _score(text, (PARAMETER_TERMS, IMPLEMENTATION_TERMS, MODULE_SIS_TERMS))
    verification_burden = 2
    if not record.get("abstract"):
        verification_burden += 1
    if not _url_or_identifier(record):
        verification_burden += 1
    if track in {TRACK_XINGYE_BRIDGE, TRACK_PRIVACY}:
        verification_burden += 1
    overclaim_risk = 1
    if track in {TRACK_MODULE_SIS, TRACK_XINGYE_BRIDGE}:
        overclaim_risk += 2
    if _contains(text, (*PROOF_TERMS, *GENERIC_RISK_TERMS)):
        overclaim_risk += 1
    return {
        "module_sis_relevance_score": min(5, module_score),
        "chameleon_hash_relevance_score": min(5, chameleon_score),
        "xingye_bridge_relevance_score": min(5, bridge_score),
        "ai4lattice_relevance_score": min(5, ai_score),
        "implementation_reproducibility_usefulness": min(5, implementation_score),
        "proof_usefulness": min(5, proof_score),
        "parameterization_usefulness": min(5, parameter_score),
        "verification_burden": min(5, verification_burden),
        "overclaim_risk": min(5, overclaim_risk),
    }


def _action_label(track: str, scores: dict[str, int]) -> str:
    if track == TRACK_EXCLUDED:
        return ACTION_EXCLUDE
    if track in {TRACK_MODULE_SIS, TRACK_XINGYE_BRIDGE}:
        return ACTION_HANDOFF_AFTER_VERIFY
    if track in {TRACK_AI4LATTICE, TRACK_PRIVACY}:
        return ACTION_KEEP_IN_RADAR
    if track == TRACK_MLKEM_MLDSA:
        if max(
            scores["implementation_reproducibility_usefulness"],
            scores["parameterization_usefulness"],
        ) >= 2:
            return ACTION_KEEP_IN_RADAR
        return ACTION_BACKLOG
    return ACTION_BACKLOG


def _target_for(track: str, action: str) -> str | None:
    if action not in {ACTION_HANDOFF_NOW, ACTION_HANDOFF_AFTER_VERIFY}:
        return None
    if track == TRACK_MODULE_SIS:
        return "research_radar/todo_verify_literature_queue.md"
    if track == TRACK_XINGYE_BRIDGE:
        return "research_radar/phase-12d-xingye-lu-bridge-handoff.md"
    return "research_radar/todo_verify_literature_queue.md"


def _todo_verify(record: dict[str, Any], track: str) -> list[str]:
    items = [
        "verify the original paper and its technical claims",
        "verify assumptions, construction type, and security model",
        "verify whether the proposed artifact use is technically justified",
    ]
    if not record.get("authors"):
        items.append("verify authors")
    if not _url_or_identifier(record):
        items.append("verify source URL or identifier")
    if track == TRACK_XINGYE_BRIDGE:
        items.append("verify the lattice/PQC technical bridge; no professor-specific fact is asserted")
    if track == TRACK_EXCLUDED:
        items.append("verify whether any explicit lattice/PQC anchor exists before reconsidering")
    return items


def _anchor_evidence(record: dict[str, Any]) -> list[str]:
    anchors = _hard_anchors(record)
    if anchors:
        return anchors
    return ["not detected; manual review required"]


def build_packet(record: dict[str, Any], week_id: str) -> dict[str, Any]:
    source_record_id = _source_record_id(record)
    track = _classify_track(record)
    scores = _scores(record, track)
    action = _action_label(track, scores)
    authors = record.get("authors")
    authors_raw: list[str] | str | None
    if isinstance(authors, list):
        authors_raw = [str(author) for author in authors]
    elif authors:
        authors_raw = str(authors)
    else:
        authors_raw = None
    return {
        "handoff_id": _packet_id(week_id, source_record_id, track),
        "week_id": week_id,
        "source_record_id": source_record_id,
        "title": str(record.get("title") or ""),
        "authors_raw": authors_raw,
        "source": str(record.get("source") or ""),
        "url_or_identifier": _url_or_identifier(record),
        "track": track,
        "action_label": action,
        "lattice_pqc_anchor_evidence": _anchor_evidence(record),
        **scores,
        "intended_research_artifact_target": _target_for(track, action),
        "todo_verify": _todo_verify(record, track),
        "non_claims": list(NON_CLAIMS),
    }


def _records_from_weekly(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    records = payload.get("records")
    if isinstance(records, list):
        candidates.extend(item for item in records if isinstance(item, dict))
    for container_name in ("sections", "report_buckets"):
        container = payload.get(container_name)
        if isinstance(container, dict):
            for value in container.values():
                if isinstance(value, list):
                    candidates.extend(item for item in value if isinstance(item, dict))
    unique: dict[str, dict[str, Any]] = {}
    for record in candidates:
        key = _source_record_id(record)
        if key not in unique:
            unique[key] = record
    return list(unique.values())


def _packet_sort_key(packet: dict[str, Any]) -> tuple[int, int, int, str]:
    action_index = ACTION_ORDER.index(packet["action_label"])
    track_index = TRACK_ORDER.index(packet["track"])
    direct_score = max(
        int(packet["module_sis_relevance_score"]),
        int(packet["chameleon_hash_relevance_score"]),
        int(packet["xingye_bridge_relevance_score"]),
        int(packet["ai4lattice_relevance_score"]),
    )
    return action_index, track_index, -direct_score, str(packet["title"]).casefold()


def build_weekly_handoff(payload: dict[str, Any], source_weekly_json: str = "") -> dict[str, Any]:
    week_id = str(payload.get("week_id") or "unknown-week")
    packets = sorted((build_packet(record, week_id) for record in _records_from_weekly(payload)), key=_packet_sort_key)
    action_counts = Counter(packet["action_label"] for packet in packets)
    track_counts = Counter(packet["track"] for packet in packets)
    excluded = [
        {
            "handoff_id": packet["handoff_id"],
            "title": packet["title"],
            "reason": "No sufficiently specific lattice/PQC-anchored handoff use was detected.",
        }
        for packet in packets
        if packet["action_label"] == ACTION_EXCLUDE
    ]
    source_health = payload.get("source_health_summary")
    handoff = {
        "schema_version": SCHEMA_VERSION,
        "week_id": week_id,
        "source_weekly_json": source_weekly_json,
        "coverage": payload.get("coverage") or {},
        "source_health_summary": source_health or {"available": False, "sources": []},
        "source_health_caveat": source_health_caveat_text(source_health if isinstance(source_health, dict) else None),
        "track_counts": dict(sorted(track_counts.items(), key=lambda item: TRACK_ORDER.index(item[0]))),
        "action_counts": dict(sorted(action_counts.items(), key=lambda item: ACTION_ORDER.index(item[0]))),
        "packets": packets,
        "excluded": excluded,
        "todo_verify": [
            "Original-paper reading is required before promoting metadata-level candidates.",
            "Handoff packets do not establish security, novelty, construction correctness, or publication readiness.",
            "ResearchArtifacts mirroring remains an explicit manual step outside this generator.",
        ],
    }
    validate_handoff_payload(handoff)
    return handoff


def validate_handoff_payload(payload: dict[str, Any]) -> None:
    missing_top_level = [field for field in TOP_LEVEL_FIELDS if field not in payload]
    if missing_top_level:
        raise ValueError(f"Weekly handoff payload is missing required fields: {', '.join(missing_top_level)}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported weekly handoff schema_version: {payload.get('schema_version')!r}")
    if not isinstance(payload["week_id"], str) or not isinstance(payload["source_weekly_json"], str):
        raise ValueError("Weekly handoff week_id and source_weekly_json must be strings.")
    for field in ("coverage", "source_health_summary", "track_counts", "action_counts"):
        if not isinstance(payload[field], dict):
            raise ValueError(f"Weekly handoff {field} must be an object.")
    for field in ("excluded", "todo_verify"):
        if not isinstance(payload[field], list):
            raise ValueError(f"Weekly handoff {field} must be a list.")
    if not isinstance(payload["source_health_caveat"], str):
        raise ValueError("Weekly handoff source_health_caveat must be a string.")
    packets = payload.get("packets")
    if not isinstance(packets, list):
        raise ValueError("Weekly handoff packets must be a list.")
    seen_ids: set[str] = set()
    for packet in packets:
        if not isinstance(packet, dict):
            raise ValueError("Each weekly handoff packet must be an object.")
        missing = [field for field in PACKET_FIELDS if field not in packet]
        if missing:
            raise ValueError(f"Weekly handoff packet is missing required fields: {', '.join(missing)}")
        handoff_id = str(packet["handoff_id"])
        if handoff_id in seen_ids:
            raise ValueError(f"Duplicate weekly handoff ID: {handoff_id}")
        seen_ids.add(handoff_id)
        if packet["track"] not in TRACK_ORDER:
            raise ValueError(f"Unsupported weekly handoff track: {packet['track']!r}")
        if packet["action_label"] not in ACTION_ORDER:
            raise ValueError(f"Unsupported weekly handoff action: {packet['action_label']!r}")
        if not isinstance(packet["lattice_pqc_anchor_evidence"], list):
            raise ValueError("Weekly handoff lattice_pqc_anchor_evidence must be a list.")
        if packet["authors_raw"] is not None and not isinstance(packet["authors_raw"], (list, str)):
            raise ValueError("Weekly handoff authors_raw must be a list, string, or null.")
        if packet["intended_research_artifact_target"] is not None and not isinstance(
            packet["intended_research_artifact_target"], str
        ):
            raise ValueError("Weekly handoff intended_research_artifact_target must be a string or null.")
        for field in SCORE_FIELDS:
            value = packet[field]
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 5:
                raise ValueError(f"Weekly handoff score {field} must be an integer from 0 to 5.")
        if not isinstance(packet["todo_verify"], list) or not isinstance(packet["non_claims"], list):
            raise ValueError("Weekly handoff todo_verify and non_claims must be lists.")
        missing_non_claims = [claim for claim in NON_CLAIMS if claim not in packet["non_claims"]]
        if missing_non_claims:
            raise ValueError("Weekly handoff packet is missing required non-claims.")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Weekly Handoff Packets - {payload['week_id']}",
        "",
        "## Executive Summary",
        "",
        f"- Total packets: {len(payload['packets'])}",
        f"- Track counts: {json.dumps(payload['track_counts'], ensure_ascii=False, sort_keys=True)}",
        f"- Action counts: {json.dumps(payload['action_counts'], ensure_ascii=False, sort_keys=True)}",
        f"- Source health caveat: {payload['source_health_caveat']}",
        "",
        "## Non-Claims",
        "",
    ]
    lines.extend(f"- {claim}" for claim in NON_CLAIMS)
    lines.extend(["", "## Handoff Packets", ""])
    if not payload["packets"]:
        lines.append("No handoff packets were generated.")
    for packet in payload["packets"]:
        lines.extend(
            [
                f"### {packet['title'] or 'Untitled'}",
                "",
                f"- Handoff ID: `{packet['handoff_id']}`",
                f"- Track: `{packet['track']}`",
                f"- Action: `{packet['action_label']}`",
                f"- Source: {packet['source'] or 'unknown'}",
                f"- URL / identifier: {packet['url_or_identifier'] or 'TODO_VERIFY'}",
                f"- Lattice/PQC anchor evidence: {', '.join(packet['lattice_pqc_anchor_evidence'])}",
                f"- Module-SIS relevance: {packet['module_sis_relevance_score']} / 5",
                f"- Chameleon hash relevance: {packet['chameleon_hash_relevance_score']} / 5",
                f"- Public Xingye bridge relevance: {packet['xingye_bridge_relevance_score']} / 5",
                f"- AI4Lattice relevance: {packet['ai4lattice_relevance_score']} / 5",
                f"- Intended ResearchArtifacts target: {packet['intended_research_artifact_target'] or 'none'}",
                "- TODO_VERIFY:",
            ]
        )
        lines.extend(f"  - {item}" for item in packet["todo_verify"])
        lines.append("")
    lines.extend(["## Excluded / Noise", ""])
    if not payload["excluded"]:
        lines.append("No excluded records.")
    else:
        lines.extend(f"- {item['title']}: {item['reason']}" for item in payload["excluded"])
    lines.extend(["", "## Global TODO_VERIFY", ""])
    lines.extend(f"- {item}" for item in payload["todo_verify"])
    lines.append("")
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    _validate_output_dir(output_dir)
    validate_handoff_payload(payload)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{payload['week_id']}-handoff-packets"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, markdown_path


def _validate_output_dir(output_dir: Path) -> None:
    parts = {part.casefold() for part in output_dir.resolve().parts}
    if "phd_application" in parts:
        raise ValueError("Refusing to write weekly handoff output into PhD_Application.")
    if ".git" in parts:
        raise ValueError("Refusing to write weekly handoff output into .git.")


def _latest_weekly_json(data_dir: Path) -> Path:
    paths = sorted(data_dir.glob("*.json"), key=lambda path: path.name)
    if not paths:
        raise FileNotFoundError(f"No weekly JSON files found under {data_dir}")
    return paths[-1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate manual weekly research handoff packets from existing weekly JSON.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--latest", action="store_true", help="Use the latest JSON under --weekly-data-dir.")
    source.add_argument("--weekly-json", type=Path, help="Read a specific weekly JSON file.")
    parser.add_argument("--weekly-data-dir", type=Path, default=Path("data") / "weekly")
    parser.add_argument("--output-dir", type=Path, default=Path("handoffs") / "weekly")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without writing files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    weekly_json = _latest_weekly_json(args.weekly_data_dir) if args.latest else args.weekly_json
    if weekly_json is None:
        raise ValueError("weekly JSON path is required")
    payload = json.loads(weekly_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("weekly JSON must contain an object")
    handoff = build_weekly_handoff(payload, source_weekly_json=weekly_json.name)
    stem = f"{handoff['week_id']}-handoff-packets"
    print(f"Weekly handoff: week={handoff['week_id']} packets={len(handoff['packets'])} output={args.output_dir}")
    if args.dry_run:
        print(f"Dry-run: would write {args.output_dir / (stem + '.json')} and {args.output_dir / (stem + '.md')}")
        return 0
    json_path, markdown_path = write_outputs(handoff, args.output_dir)
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
