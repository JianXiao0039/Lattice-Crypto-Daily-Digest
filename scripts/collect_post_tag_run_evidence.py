from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "JianXiao0039/Lattice-Crypto-Daily-Digest"
TAG = "v0.4.0"
EVIDENCE_CLASSES = {
    "automation_post_tag_actual",
    "manual_post_tag_equivalent",
    "pre_tag_baseline",
    "historical_ci_evidence",
    "synthetic_test_fixture",
    "unknown",
}


def run_git(project_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def tag_info(project_root: Path) -> dict[str, Any]:
    commit = run_git(project_root, "rev-list", "-n", "1", TAG)
    timestamp = run_git(project_root, "show", "-s", "--format=%cI", TAG)
    object_type = run_git(project_root, "cat-file", "-t", TAG)
    pyproject = run_git(project_root, "show", f"{TAG}:pyproject.toml")
    package_version = "unknown"
    for line in pyproject.splitlines():
        if line.strip().startswith("version ="):
            package_version = line.split("=", 1)[1].strip().strip('"')
            break
    return {
        "tag": TAG,
        "target_commit": commit,
        "timestamp": timestamp,
        "object_type": object_type,
        "package_version": package_version,
    }


def load_daily(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"records": payload, "metadata": {}, "source_health": []}


def source_summary(payload: dict[str, Any]) -> dict[str, int]:
    health = list(payload.get("source_health") or (payload.get("metadata") or {}).get("source_health") or [])
    statuses = [str(item.get("status") or item.get("health_status") or "unknown") for item in health]
    return {name: statuses.count(name) for name in ("green", "yellow", "red", "unknown")}


def source_entry(payload: dict[str, Any], name: str) -> dict[str, Any]:
    health = list(payload.get("source_health") or (payload.get("metadata") or {}).get("source_health") or [])
    return next((item for item in health if item.get("source") == name), {})


def artifact_evidence(project_root: Path, tag_timestamp: str) -> list[dict[str, Any]]:
    tag_dt = datetime.fromisoformat(tag_timestamp)
    paths = sorted((project_root / "data").glob("????-??-??.json"))
    rows: list[dict[str, Any]] = []
    for path in paths:
        payload = load_daily(path)
        metadata = payload.get("metadata") or {}
        records = list(payload.get("records") or [])
        run_date = str(metadata.get("run_date") or metadata.get("target_date") or path.stem)
        try:
            run_dt = datetime.fromisoformat(f"{run_date}T23:59:59+08:00")
        except ValueError:
            run_dt = None
        evidence_class = "pre_tag_baseline" if run_dt and run_dt < tag_dt else "unknown"
        collector = metadata.get("collector")
        if run_dt and run_dt >= tag_dt:
            if collector == "github_actions":
                evidence_class = "automation_post_tag_actual"
            elif collector == "local_codex":
                evidence_class = "manual_post_tag_equivalent"
        health = source_summary(payload)
        total = sum(health.values())
        source_starved = bool(not records and total and health["red"] == total)
        iacr = source_entry(payload, "iacr_eprint")
        semantic = source_entry(payload, "semantic_scholar")
        commit = run_git(project_root, "log", "-1", "--format=%H", "--", path.relative_to(project_root).as_posix())
        rows.append(
            {
                "observation_id": f"daily-artifact-{path.stem}",
                "date_time": run_date,
                "evidence_class": evidence_class,
                "artifact_date": path.stem,
                "artifact_path": path.relative_to(project_root).as_posix(),
                "commit_hash": commit or None,
                "tag_relative_status": "before_tag" if evidence_class == "pre_tag_baseline" else "after_tag_or_unknown",
                "workflow_run_identifier": None,
                "automation_name": "Daily Public Digest Run" if collector == "github_actions" else "manual/local daily run",
                "source_health_summary": health,
                "record_count": len(records),
                "source_starved_status": source_starved,
                "iacr_status": iacr.get("latest_feed_status") or "unknown",
                "semantic_scholar_status": semantic.get("status") or semantic.get("health_status") or "unknown",
                "validation_status": "persisted_daily_artifact",
                "confidence": "high" if evidence_class != "unknown" else "low",
                "evidence_source": "daily JSON metadata plus Git history",
                "TODO_VERIFY": [] if evidence_class != "unknown" else ["run provenance requires verification"],
            }
        )
    return rows


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "lattice-digest-phase12y"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def post_tag_workflow_evidence(tag_timestamp: str) -> tuple[list[dict[str, Any]], list[str]]:
    tag_dt = datetime.fromisoformat(tag_timestamp)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    try:
        payload = fetch_json(f"https://api.github.com/repos/{REPOSITORY}/actions/runs?per_page=50")
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return rows, [f"GitHub Actions API unavailable: {type(exc).__name__}"]
    for run in payload.get("workflow_runs") or []:
        started = run.get("run_started_at") or run.get("created_at")
        if not started:
            continue
        started_dt = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
        if started_dt <= tag_dt:
            continue
        name = str(run.get("name") or "unknown")
        evidence_class = "automation_post_tag_actual" if name == "Daily Lattice Crypto Digest" else "historical_ci_evidence"
        validation = str(run.get("conclusion") or run.get("status") or "unknown")
        todo: list[str] = []
        details: dict[str, Any] = {}
        if name == "Daily Lattice Crypto Digest":
            try:
                jobs = fetch_json(str(run.get("jobs_url")))
                job = (jobs.get("jobs") or [{}])[0]
                steps = {str(step.get("name")): step.get("conclusion") for step in job.get("steps") or []}
                details["step_conclusions"] = steps
                if steps.get("Run daily digest") == "success" and steps.get("Verify generated artifacts") == "success":
                    validation = "generated_and_verified_ephemeral"
                if steps.get("Commit generated digest") == "failure":
                    validation += "_commit_failed"
                    todo.append("exact commit/push failure log requires authenticated GitHub access")
            except (OSError, urllib.error.URLError, json.JSONDecodeError, TypeError) as exc:
                todo.append(f"job-step evidence unavailable: {type(exc).__name__}")
        rows.append(
            {
                "observation_id": f"github-run-{run.get('id')}",
                "date_time": started,
                "evidence_class": evidence_class,
                "artifact_date": started_dt.date().isoformat() if name == "Daily Lattice Crypto Digest" else None,
                "artifact_path": "data/YYYY-MM-DD.json and digests/YYYY-MM-DD.md" if name == "Daily Lattice Crypto Digest" else None,
                "commit_hash": run.get("head_sha"),
                "tag_relative_status": "after_tag",
                "workflow_run_identifier": str(run.get("id")),
                "automation_name": name,
                "source_health_summary": None,
                "record_count": None,
                "source_starved_status": "unknown",
                "iacr_status": "unknown",
                "semantic_scholar_status": "unknown",
                "validation_status": validation,
                "confidence": "high",
                "evidence_source": run.get("html_url") or "GitHub Actions public API",
                "details": details,
                "TODO_VERIFY": todo,
            }
        )
    return rows, warnings


def manual_handoff_evidence(project_root: Path, tag_timestamp: str) -> list[dict[str, Any]]:
    report = project_root / "docs" / "reports" / "phase-12v-post-tag-validation-log.md"
    handoff = project_root / "handoffs" / "weekly" / "2026-W23-handoff-packets.json"
    if not report.exists() or not handoff.exists():
        return []
    text = report.read_text(encoding="utf-8")
    if "weekly handoff generation | pass; 2026-W23, 20 packets" not in text:
        return []
    payload = json.loads(handoff.read_text(encoding="utf-8"))
    return [
        {
            "observation_id": "manual-weekly-handoff-phase-12v",
            "date_time": "2026-06-11",
            "evidence_class": "manual_post_tag_equivalent",
            "artifact_date": payload.get("week_id"),
            "artifact_path": handoff.relative_to(project_root).as_posix(),
            "commit_hash": None,
            "tag_relative_status": "after_tag",
            "workflow_run_identifier": None,
            "automation_name": "manual weekly handoff replay",
            "source_health_summary": payload.get("source_health_summary"),
            "record_count": len(payload.get("packets") or []),
            "source_starved_status": False,
            "iacr_status": "inherited_from_weekly_input",
            "semantic_scholar_status": "inherited_from_weekly_input",
            "validation_status": "20_packets_generated_from_stale_W23_input",
            "confidence": "high",
            "evidence_source": report.relative_to(project_root).as_posix(),
            "TODO_VERIFY": ["not an actual Weekly Public Synthesis run", "W23 input covered only 5 of 7 days"],
        }
    ]


def build_ledger(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    tag = tag_info(project_root)
    artifacts = artifact_evidence(project_root, tag["timestamp"])
    workflow_rows, warnings = post_tag_workflow_evidence(tag["timestamp"])
    rows = artifacts + manual_handoff_evidence(project_root, tag["timestamp"]) + workflow_rows
    for row in rows:
        if row["evidence_class"] not in EVIDENCE_CLASSES:
            raise ValueError(f"invalid evidence class: {row['evidence_class']}")
    counts = {name: sum(1 for row in rows if row["evidence_class"] == name) for name in sorted(EVIDENCE_CLASSES)}
    return {"schema_version": 1, "tag": tag, "counts": counts, "observations": rows, "warnings": warnings}


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Post-Tag Run Evidence Ledger",
        "",
        f"- tag target: `{payload['tag']['target_commit']}`",
        f"- tag timestamp: `{payload['tag']['timestamp']}`",
        f"- tag package version: `{payload['tag']['package_version']}`",
        "",
        "## Counts",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in payload["counts"].items())
    lines.extend(
        [
            "",
            "| observation | time | class | automation | artifact | validation | confidence | TODO_VERIFY |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in payload["observations"]:
        lines.append(
            "| {id} | {time} | {cls} | {automation} | {artifact} | {validation} | {confidence} | {todo} |".format(
                id=row["observation_id"],
                time=row["date_time"],
                cls=row["evidence_class"],
                automation=row["automation_name"],
                artifact=row["artifact_path"] or "none",
                validation=row["validation_status"],
                confidence=row["confidence"],
                todo="; ".join(row["TODO_VERIFY"]) or "none",
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    print(render_markdown(build_ledger()), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
