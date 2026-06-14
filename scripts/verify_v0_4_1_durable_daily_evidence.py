from __future__ import annotations

import json
import re
import subprocess
import tomllib
from datetime import date
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.4.1"
HISTORICAL_TAG = "v0.4.0"
HISTORICAL_TARGET = "08c5f07967739ecd008773c4b167cd736848df88"
CORRECTIVE_TAG = "v0.4.1"
DATE_PATTERN = re.compile(r"^(?:data|digests)/(\d{4}-\d{2}-\d{2})\.(?:json|md)$")


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _version_from_init(path: Path) -> str:
    match = re.search(r'__version__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"missing __version__: {path}")
    return match.group(1)


def read_versions(root: Path = ROOT) -> dict[str, str]:
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    versions = {
        "pyproject": str(pyproject["project"]["version"]),
        "source_package": _version_from_init(root / "src/lattice_digest/__init__.py"),
    }
    bridge = root / "lattice_digest/__init__.py"
    versions["bridge_package"] = _version_from_init(bridge) if bridge.exists() else "missing"
    return versions


def _daily_pairs(paths: list[str], *, minimum_date: date) -> list[dict[str, Any]]:
    by_date: dict[str, set[str]] = {}
    for path in paths:
        normalized = path.strip().replace("\\", "/")
        match = DATE_PATTERN.match(normalized)
        if not match:
            continue
        artifact_date = date.fromisoformat(match.group(1))
        if artifact_date < minimum_date:
            continue
        by_date.setdefault(match.group(1), set()).add(normalized.split("/", 1)[0])
    return [
        {
            "target_date": target_date,
            "markdown_path": f"digests/{target_date}.md",
            "json_path": f"data/{target_date}.json",
            "markdown_present": "digests" in kinds,
            "json_present": "data" in kinds,
            "pair_complete": kinds == {"data", "digests"},
        }
        for target_date, kinds in sorted(by_date.items())
    ]


def classify_evidence(
    *,
    remote_pairs: list[dict[str, Any]],
    retained_manifests: list[dict[str, Any]],
) -> str:
    complete_paths = {
        (item["markdown_path"], item["json_path"])
        for item in remote_pairs
        if item["pair_complete"]
    }
    durable_classes = {
        "durable_automation_post_tag_actual",
        "durable_manual_post_tag_equivalent",
    }
    for manifest in retained_manifests:
        evidence_class = manifest.get("evidence_class")
        required_values = (
            manifest.get("run_identifier"),
            manifest.get("target_date"),
            manifest.get("markdown_path"),
            manifest.get("json_path"),
            manifest.get("source_health_summary"),
            manifest.get("validation_result"),
            manifest.get("ci_traceability"),
        )
        pair = (manifest.get("markdown_path"), manifest.get("json_path"))
        if (
            evidence_class in durable_classes
            and all(value not in (None, "", [], {}) for value in required_values)
            and manifest.get("git_persistence") is True
            and manifest.get("origin_main_verification") is True
            and pair in complete_paths
        ):
            return str(evidence_class)
    return "insufficient_evidence"


def _load_origin_manifests(
    run_git: Callable[..., str],
    paths: list[str],
) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for path in paths:
        try:
            payload = json.loads(run_git("show", f"origin/main:{path}"))
        except (RuntimeError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            manifests.append(payload)
    return manifests


def build_report(
    root: Path = ROOT,
    *,
    git: Callable[..., str] | None = None,
) -> dict[str, Any]:
    run_git = git or (lambda *args: _git(root, *args))
    versions = read_versions(root)
    historical_target = run_git("rev-parse", f"{HISTORICAL_TAG}^{{}}")
    corrective_target = run_git("rev-parse", f"{CORRECTIVE_TAG}^{{}}")
    corrective_time = run_git("show", "-s", "--format=%cI", f"{CORRECTIVE_TAG}^{{}}")
    minimum_date = date.fromisoformat(corrective_time[:10])
    head = run_git("rev-parse", "HEAD")
    origin_main = run_git("rev-parse", "origin/main")
    origin_paths = [
        line for line in run_git("ls-tree", "-r", "--name-only", "origin/main").splitlines() if line
    ]
    local_paths = [line for line in run_git("ls-files").splitlines() if line]
    remote_pairs = _daily_pairs(origin_paths, minimum_date=minimum_date)
    local_pairs = _daily_pairs(local_paths, minimum_date=minimum_date)
    retained_manifest_paths = sorted(
        path
        for path in origin_paths
        if path.startswith("docs/research_tracks/v0.4.1_durable_daily_evidence_manifest")
        and path.endswith(".json")
    )
    retained_manifests = _load_origin_manifests(run_git, retained_manifest_paths)
    evidence_class = classify_evidence(
        remote_pairs=remote_pairs,
        retained_manifests=retained_manifests,
    )
    durable = evidence_class in {
        "durable_automation_post_tag_actual",
        "durable_manual_post_tag_equivalent",
    }
    complete_remote_pairs = [item for item in remote_pairs if item["pair_complete"]]
    return {
        "schema_version": 1,
        "verification_type": "read_only_git_evidence_audit",
        "active_versions": versions,
        "active_version_consistent": all(value == EXPECTED_VERSION for value in versions.values()),
        "historical_tag": {
            "name": HISTORICAL_TAG,
            "target": historical_target,
            "immutable_target_ok": historical_target == HISTORICAL_TARGET,
        },
        "corrective_tag": {
            "name": CORRECTIVE_TAG,
            "exists": True,
            "target": corrective_target,
            "target_commit_time": corrective_time,
        },
        "head": head,
        "origin_main": origin_main,
        "head_matches_origin_main": head == origin_main,
        "minimum_artifact_date": minimum_date.isoformat(),
        "origin_main_daily_candidates": remote_pairs,
        "origin_main_complete_pairs": complete_remote_pairs,
        "tracked_local_daily_candidates": local_pairs,
        "retained_evidence_manifest_paths_in_origin": retained_manifest_paths,
        "retained_evidence_manifests_in_origin": retained_manifests,
        "evidence_class": evidence_class,
        "durable_daily_evidence_exists": durable,
        "run_identifier": None,
        "automation_name": None,
        "target_date": complete_remote_pairs[-1]["target_date"] if complete_remote_pairs else None,
        "markdown_path": complete_remote_pairs[-1]["markdown_path"] if complete_remote_pairs else None,
        "json_path": complete_remote_pairs[-1]["json_path"] if complete_remote_pairs else None,
        "source_health_summary": None,
        "validation_result": None,
        "origin_main_verification": bool(complete_remote_pairs),
        "ci_traceability": None,
        "confidence": "high" if not complete_remote_pairs else "medium",
        "TODO_VERIFY": [
            "A durable class requires an identifiable run, source-health evidence, validation, and CI traceability.",
            "No complete post-v0.4.1 Markdown/JSON pair is present in origin/main."
            if not complete_remote_pairs
            else "Confirm that the complete pair belongs to an identifiable validated Daily run.",
        ],
    }


def main() -> int:
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
