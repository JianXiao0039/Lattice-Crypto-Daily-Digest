from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
import urllib.parse
import xml.etree.ElementTree as ET

import requests

from lattice_digest.ontology_v3 import load_ontology_v3
from lattice_digest.query_portfolio_v3 import load_query_portfolio_v3
from lattice_digest.sources.arxiv import parse_arxiv_atom


ROOT = Path(__file__).resolve().parents[1]
V1_FIXTURE = ROOT / "tests" / "fixtures" / "retrieval_benchmark_v1.json"
DEFAULT_OUTPUT = ROOT / "tests" / "fixtures" / "recent_paper_benchmark_v2.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze Retrieval Benchmark V2 from bounded configured-source snapshots.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--real-target", type=int, default=160)
    parser.add_argument("--synthetic-target", type=int, default=40)
    parser.add_argument("--per-family", type=int, default=25)
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    portfolio = load_query_portfolio_v3()
    ontology = load_ontology_v3()
    queries = [
        query
        for query in portfolio.compile_for_sources(["arxiv"])
        if query.intent != "OFFICIAL_METADATA_WATCH"
    ]
    records_by_id: dict[str, dict] = {}
    failures: list[dict[str, str]] = []
    observed_at = datetime.now(timezone.utc).isoformat()
    session = requests.Session()
    session.headers["User-Agent"] = "lattice-crypto-daily-digest-benchmark-v2/1.0 (bounded fixture build)"
    for query in queries:
        params = urllib.parse.urlencode(
            {
                "search_query": query.native_semantics,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": min(max(args.per_family, 1), 50),
            }
        )
        url = f"https://export.arxiv.org/api/query?{params}"
        try:
            response = session.get(url, timeout=40)
            response.raise_for_status()
            source_records = parse_arxiv_atom(response.text)
        except (requests.RequestException, ET.ParseError, ValueError) as exc:
            failures.append({"query_id": query.query_id, "error": f"{type(exc).__name__}: {exc}"})
            time.sleep(args.delay_seconds)
            continue
        accepted_for_family = 0
        for record in source_records:
            if not record.arxiv_id or not record.source_url or not record.publication_date:
                continue
            key = record.arxiv_id.lower()
            if key in records_by_id:
                continue
            analysis = ontology.analyze_fields(
                title=record.title,
                abstract=record.abstract,
                keywords=record.categories,
            )
            source_concepts = list(analysis.source_concept_ids)
            core = [item for item in source_concepts if item.split(".", 1)[0] in {"FND", "HARD", "RED", "ATTACK", "PRIM", "PROOF", "FHE", "IMPL", "AI4LC", "STD"}]
            reduction_only = bool(core) and all(item.startswith("RED.") for item in core)
            evidence_text = f"{record.title} {record.abstract}".lower()
            explicit_lattice_consequence = any(
                anchor in evidence_text
                for anchor in (
                    "learning with errors", " lwe ", "shortest vector", " svp ", "lattice reduction",
                    "lattice problem", "ideal lattice", "module lattice", "ntru", "regev's reduction",
                )
            )
            relevance = (
                "A"
                if core and not analysis.hard_negative_matches and not (reduction_only and not explicit_lattice_consequence)
                else "D"
            )
            topic_axes = sorted(
                {
                    ontology.by_id[concept_id].domain
                    for concept_id in core
                    if concept_id in ontology.by_id
                }
            ) or ["generic_math_negative"]
            records_by_id[key] = _real_record(
                record,
                query=query,
                observed_at=observed_at,
                source_concepts=source_concepts,
                topic_axes=topic_axes,
                relevance=relevance,
            )
            accepted_for_family += 1
            if accepted_for_family >= args.per_family:
                break
        time.sleep(args.delay_seconds)

    real_records = _balanced_real_records(list(records_by_id.values()), args.real_target)
    _assign_evaluation_windows(real_records)
    synthetic_records = _synthetic_controls(args.synthetic_target, observed_at)
    all_records = [*real_records, *synthetic_records]
    payload = {
        "schema_version": "2.0",
        "benchmark_id": "RECENT_PAPER_BENCHMARK_V2",
        "metric_scope": "configured_source_snapshot_benchmark_not_open_web_recall",
        "target_record_count": 200,
        "real_record_target": args.real_target,
        "synthetic_record_limit": 40,
        "generated_at": observed_at,
        "source_build_failures": failures,
        "records": all_records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "records": len(all_records),
        "real": len(real_records),
        "synthetic": len(synthetic_records),
        "verified_real_deficit": max(0, args.real_target - len(real_records)),
        "source_build_failures": failures,
    }, ensure_ascii=False, indent=2))
    return 0 if len(real_records) >= args.real_target else 2


def _real_record(record, *, query, observed_at: str, source_concepts: list[str], topic_axes: list[str], relevance: str) -> dict:
    return {
        "fixture_id": f"RBV2-REAL-{record.arxiv_id.replace('/', '-')}",
        "record_kind": "real_research",
        "paper_id": f"arxiv:{record.arxiv_id}",
        "title": record.title,
        "identifiers": {"arxiv_id": record.arxiv_id, "doi": record.doi, "eprint_id": None},
        "source_snapshots": [
            {
                "source": "arxiv",
                "source_url": record.source_url,
                "pdf_url": record.pdf_url,
                "paper_id": f"arxiv:{record.arxiv_id}",
                "identifiers": {"arxiv_id": record.arxiv_id, "doi": record.doi, "eprint_id": None},
                "title": record.title,
                "authors": record.authors,
                "abstract": record.abstract,
                "categories": record.categories,
                "dates": {
                    "publication": record.publication_date,
                    "publication_timestamp": record.publication_timestamp,
                    "publication_semantics": "AUTHORITATIVE_PUBLICATION_DATE",
                    "revision": record.update_date,
                    "revision_timestamp": record.update_timestamp,
                    "revision_semantics": "AUTHORITATIVE_CONTENT_REVISION_DATE",
                },
                "query_id": query.query_id,
                "query_family": query.family_id,
                "query_expression": query.native_semantics,
                "observed_at": observed_at,
                "content_hash": _hash(record.title + "\n" + record.abstract),
            }
        ],
        "evaluation_as_of": observed_at,
        "relevance_expected": relevance,
        "daily_freshness_expected": False,
        "critical_expected": False,
        "topic_axes": topic_axes,
        "expected_route": "OBSERVED_RELEVANT_STALE" if relevance != "D" else "OBSERVED_IRRELEVANT",
        "evidence_required": ["official arXiv title", "official arXiv abstract", "authoritative publication timestamp"],
        "historical_only": False,
        "metadata_update_only": False,
        "challenge_tags": [
            *( ["title_weak"] if not any(term.lower() in record.title.lower() for term in ("lattice", "lwe", "sis", "ntru", "bkz", "fhe", "kyber", "dilithium")) else [] ),
            *( ["indirect_consequence"] if query.intent == "DISCOVERY_RELATION" else [] ),
        ],
        "expected_consequence_edges": [],
        "adjudication_provenance": {
            "source": "official arXiv Atom API snapshot",
            "method": "Codex source-evidence adjudication using frozen Ontology V3; challenge sample requires manual review",
            "observed_at": observed_at,
        },
    }


def _assign_evaluation_windows(records: list[dict]) -> None:
    for index, item in enumerate(records):
        publication = datetime.fromisoformat(item["source_snapshots"][0]["dates"]["publication_timestamp"].replace("Z", "+00:00"))
        if index < max(0, len(records) - 40) and item["relevance_expected"] != "D":
            evaluation = publication + timedelta(hours=24)
            item["daily_freshness_expected"] = True
            item["expected_route"] = "PRIMARY_NEW"
        else:
            evaluation = datetime(2026, 8, 28, 12, tzinfo=timezone.utc)
            fresh = publication >= evaluation - timedelta(hours=36) and publication <= evaluation
            item["daily_freshness_expected"] = bool(fresh and item["relevance_expected"] != "D")
            item["historical_only"] = not fresh and item["relevance_expected"] != "D"
            item["expected_route"] = (
                "PRIMARY_NEW" if item["daily_freshness_expected"] else
                "OBSERVED_RELEVANT_STALE" if item["relevance_expected"] != "D" else
                "OBSERVED_IRRELEVANT"
            )
        item["evaluation_as_of"] = evaluation.isoformat()


def _balanced_real_records(records: list[dict], target: int) -> list[dict]:
    by_family: dict[str, list[dict]] = {}
    for item in records:
        family = item["source_snapshots"][0]["query_family"]
        by_family.setdefault(family, []).append(item)
    for items in by_family.values():
        items.sort(key=lambda item: item["paper_id"])
    selected: list[dict] = []
    while len(selected) < target:
        progress = False
        for family in sorted(by_family):
            if len(selected) >= target:
                break
            if by_family[family]:
                selected.append(by_family[family].pop(0))
                progress = True
        if not progress:
            break
    return selected


def _synthetic_controls(limit: int, observed_at: str) -> list[dict]:
    payload = json.loads(V1_FIXTURE.read_text(encoding="utf-8"))
    priority_ids = ["SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"]
    selected = [next(item for item in payload["records"] if item["fixture_id"] == fixture_id) for fixture_id in priority_ids]
    # Keep the synthetic slice adversarial but balanced across ontology domains.
    # These are explicitly synthetic V1 controls, never represented as real hits.
    category_order = (
        "lwe_rlwe_mlwe_positive",
        "sis_module_sis_positive",
        "lattice_reduction_positive",
        "cryptanalysis_positive",
        "zk_lattice_positive",
        "lattice_signature_ch_positive",
        "fhe_lattice_he_positive",
        "ai4lc_positive",
        "pqc_standard_positive",
        "indirect_quantum_lattice_positive",
        "generic_quantum_negative",
        "generic_ai_negative",
        "generic_cybersecurity_negative",
        "strong_venue_irrelevant_negative",
        "ambiguous_boundary",
        "title_evidence_contrast",
    )
    by_category = {
        category: [
            item for item in payload["records"]
            if item.get("primary_benchmark_category") == category and item not in selected
        ]
        for category in category_order
    }
    while len(selected) < limit:
        progress = False
        for category in category_order:
            if len(selected) >= limit:
                break
            if by_category[category]:
                selected.append(by_category[category].pop(0))
                progress = True
        if not progress:
            break
    controls: list[dict] = []
    category_axes = {
        "lwe_rlwe_mlwe_positive": "foundations_hardness",
        "sis_module_sis_positive": "foundations_hardness",
        "lattice_reduction_positive": "cryptanalysis",
        "cryptanalysis_positive": "cryptanalysis",
        "zk_lattice_positive": "zk_proofs",
        "lattice_signature_ch_positive": "pqc_primitives",
        "fhe_lattice_he_positive": "fhe",
        "ai4lc_positive": "ai4lc",
        "pqc_standard_positive": "standards_ecosystem",
        "indirect_quantum_lattice_positive": "reductions_complexity",
        "generic_quantum_negative": "generic_quantum_negative",
        "generic_ai_negative": "generic_math_negative",
        "generic_cybersecurity_negative": "generic_crypto_negative",
        "strong_venue_irrelevant_negative": "generic_math_negative",
        "ambiguous_boundary": "generic_math_negative",
        "title_evidence_contrast": "generic_crypto_negative",
        "critical_security_positive": "reductions_complexity",
    }
    for index, item in enumerate(selected[:limit]):
        is_simon = item["fixture_id"] == "SIMON_DCP_2026_CANARY_MUST_NOT_BE_MISSED"
        category = item.get("primary_benchmark_category", "ambiguous_boundary")
        axis = category_axes[category]
        relevant = bool(item.get("expected", {}).get("relevant"))
        publication = item.get("publication_date", "2026-08-11")
        controls.append(
            {
                "fixture_id": f"RBV2-SYN-{index + 1:03d}",
                "record_kind": "synthetic_adversarial_control",
                "paper_id": f"synthetic:{index + 1:03d}",
                "title": item["title"],
                "identifiers": {"arxiv_id": None, "doi": None, "eprint_id": None},
                "source_snapshots": [
                    {
                        "source": "offline_benchmark",
                        "source_url": f"https://example.invalid/retrieval-benchmark-v2/{index + 1:03d}",
                        "paper_id": f"synthetic:{index + 1:03d}",
                        "identifiers": {},
                        "title": item["title"],
                        "authors": item.get("authors", []),
                        "abstract": item.get("abstract", ""),
                        "categories": ["synthetic_adversarial_control"],
                        "dates": {
                            "publication": publication,
                            "publication_timestamp": f"{publication}T00:00:00Z",
                            "publication_semantics": "AUTHORITATIVE_PUBLICATION_DATE",
                            "revision": None,
                            "revision_timestamp": None,
                            "revision_semantics": "AUTHORITATIVE_CONTENT_REVISION_DATE",
                        },
                        "query_id": "synthetic-control",
                        "query_family": "synthetic_adversarial_control",
                        "query_expression": "not a production query",
                        "observed_at": observed_at,
                        "content_hash": _hash(item["title"] + "\n" + item.get("abstract", "")),
                    }
                ],
                "evaluation_as_of": "2026-08-28T12:00:00+00:00",
                "relevance_expected": "A" if relevant else "D",
                "daily_freshness_expected": False,
                "critical_expected": is_simon,
                "topic_axes": [axis],
                "expected_route": "CRITICAL_NEWLY_OBSERVED_VERIFY_FIRST" if is_simon else "OBSERVED_IRRELEVANT",
                "evidence_required": ["complete frozen synthetic evidence; never a real source hit"],
                "historical_only": relevant,
                "metadata_update_only": False,
                "challenge_tags": (
                    ["title_weak", "indirect_consequence"]
                    if is_simon or category == "indirect_quantum_lattice_positive"
                    else ["false_positive_control"] if not relevant
                    else ["synthetic_domain_control"]
                ),
                "expected_consequence_edges": ["SOLVES:DCP", "AFFECTS_SECURITY:SVP", "AFFECTS_SECURITY:LWE"] if is_simon else [],
                "adjudication_provenance": {
                    "source": "Retrieval Benchmark V1 synthetic control",
                    "method": "explicitly synthetic deterministic adversarial control",
                    "observed_at": observed_at,
                },
            }
        )
    return controls


def _hash(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
