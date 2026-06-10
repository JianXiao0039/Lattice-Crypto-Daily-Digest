from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from lattice_digest.weekly_handoff import (
    NON_CLAIMS,
    PACKET_FIELDS,
    TRACK_EXCLUDED,
    TRACK_MODULE_SIS,
    TRACK_XINGYE_BRIDGE,
    build_weekly_handoff,
    main,
    render_markdown,
    validate_handoff_payload,
    write_outputs,
)


def _record(title: str, abstract: str, *, source_url: str | None = None) -> dict[str, object]:
    return {
        "dedup_key": f"title:{title.lower()}",
        "title": title,
        "authors": ["Alice Example"],
        "abstract": abstract,
        "source": "fixture",
        "source_url": source_url or f"https://example.org/{title.lower().replace(' ', '-')}",
        "relevance_label": "A",
        "relevance_score": 90,
        "taxonomy_tags": [],
        "tags": [],
        "research_sections": [],
        "ranking_explanation": {"matched_taxonomy": [], "positive_signals": [], "negative_signals": []},
    }


def _weekly(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "week_id": "2026-W23",
        "coverage": {"expected_days": 7, "loaded_days": [], "missing_days": []},
        "sections": {"Fixture": records},
        "source_health_summary": {"available": False, "sources": [], "note": "No source health fixture."},
    }


def test_generates_valid_handoff_json_for_sample_weekly_records() -> None:
    payload = build_weekly_handoff(
        _weekly([_record("Module-SIS chameleon hash", "A Module-SIS lattice chameleon hash construction.")]),
        "2026-W23.json",
    )
    assert payload["schema_version"] == 1
    assert payload["week_id"] == "2026-W23"
    assert len(payload["packets"]) == 1
    packet = payload["packets"][0]
    for field in PACKET_FIELDS:
        assert field in packet
    assert packet["non_claims"] == NON_CLAIMS
    validate_handoff_payload(payload)


def test_generates_valid_markdown() -> None:
    payload = build_weekly_handoff(_weekly([_record("Module-SIS chameleon hash", "Module-SIS lattice commitment.")]))
    markdown = render_markdown(payload)
    assert "# Weekly Handoff Packets - 2026-W23" in markdown
    assert "## Non-Claims" in markdown
    assert "## Handoff Packets" in markdown
    assert "this is not a security proof" in markdown
    assert "this is not a claim that a PI works on a topic" in markdown


def test_includes_module_sis_chameleon_hash_anchored_candidate() -> None:
    payload = build_weekly_handoff(
        _weekly([_record("Module-SIS chameleon hash", "Module-SIS trapdoor collision and lattice commitment.")])
    )
    packet = payload["packets"][0]
    assert packet["track"] == TRACK_MODULE_SIS
    assert packet["action_label"] == "handoff_after_verify"
    assert packet["module_sis_relevance_score"] >= 3
    assert packet["chameleon_hash_relevance_score"] >= 1


@pytest.mark.parametrize(
    ("title", "abstract"),
    [
        ("A generic hash method", "A generic hash for databases."),
        ("A generic commitment protocol", "A commitment protocol for database records."),
        ("Private registration workflow", "A registration workflow for accounts."),
        ("AI optimization for blockchains", "A deep learning optimization method for blockchains."),
        ("A zero-knowledge credential", "An anonymous credential with a zero-knowledge proof."),
    ],
)
def test_excludes_generic_hash_and_commitment_without_lattice_anchor(title: str, abstract: str) -> None:
    packet = build_weekly_handoff(_weekly([_record(title, abstract)]))["packets"][0]
    assert packet["track"] == TRACK_EXCLUDED
    assert packet["action_label"] == "exclude"


def test_broad_weekly_section_is_not_hard_handoff_evidence() -> None:
    record = _record("A generic database protocol", "A database protocol.")
    record["research_sections"] = ["SIS / NTRU / Commitments / Chameleon Hash"]
    packet = build_weekly_handoff(_weekly([record]))["packets"][0]
    assert packet["track"] == TRACK_EXCLUDED
    assert packet["action_label"] == "exclude"


def test_marks_xingye_bridge_candidate_todo_verify_not_verified_fact() -> None:
    packet = build_weekly_handoff(
        _weekly(
            [
                _record(
                    "Lattice-based linkable ring signature",
                    "A post-quantum lattice-based linkable ring signature construction.",
                )
            ]
        )
    )["packets"][0]
    assert packet["track"] == TRACK_XINGYE_BRIDGE
    assert packet["action_label"] == "handoff_after_verify"
    assert any("no professor-specific fact" in item for item in packet["todo_verify"])
    assert all("Xingye Lu works" not in item for item in packet["todo_verify"])


def test_handles_empty_weekly_input() -> None:
    payload = build_weekly_handoff(_weekly([]))
    assert payload["packets"] == []
    assert payload["excluded"] == []
    assert "source_health_caveat" in payload
    assert "No handoff packets were generated." in render_markdown(payload)
    validate_handoff_payload(payload)


def test_reads_report_buckets_when_sections_are_missing() -> None:
    record = _record("Module-SIS chameleon hash", "A Module-SIS lattice chameleon hash construction.")
    weekly = _weekly([])
    weekly.pop("sections")
    weekly["report_buckets"] = {"High-Priority Papers": [record]}
    packet = build_weekly_handoff(weekly)["packets"][0]
    assert packet["track"] == TRACK_MODULE_SIS


def test_dry_run_writes_no_files_and_does_not_modify_weekly_input() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly_dir = root / "data" / "weekly"
        weekly_dir.mkdir(parents=True)
        weekly_path = weekly_dir / "2026-W23.json"
        weekly_path.write_text(json.dumps(_weekly([_record("Module-SIS chameleon hash", "Module-SIS.")])) , encoding="utf-8")
        before = weekly_path.read_bytes()
        output_dir = root / "handoffs" / "weekly"
        result = main(
            [
                "--weekly-json",
                str(weekly_path),
                "--output-dir",
                str(output_dir),
                "--dry-run",
            ]
        )
        assert result == 0
        assert not output_dir.exists()
        assert weekly_path.read_bytes() == before


def test_writes_json_and_markdown_without_network() -> None:
    with TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "handoffs" / "weekly"
        payload = build_weekly_handoff(_weekly([_record("Module-SIS chameleon hash", "Module-SIS.")]))
        json_path, markdown_path = write_outputs(payload, output_dir)
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
        assert loaded["week_id"] == "2026-W23"
        assert markdown_path.read_text(encoding="utf-8").startswith("# Weekly Handoff Packets")


def test_serialized_outputs_are_stable() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        payload = build_weekly_handoff(_weekly([_record("Module-SIS chameleon hash", "Module-SIS.")]))
        first_json, first_markdown = write_outputs(payload, root / "first")
        second_json, second_markdown = write_outputs(payload, root / "second")
        assert first_json.read_bytes() == second_json.read_bytes()
        assert first_markdown.read_bytes() == second_markdown.read_bytes()


def test_cli_requires_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr("socket.create_connection", fail_network)
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        weekly_path = root / "2026-W23.json"
        weekly_path.write_text(json.dumps(_weekly([_record("Module-SIS chameleon hash", "Module-SIS.")])), encoding="utf-8")
        assert main(["--weekly-json", str(weekly_path), "--output-dir", str(root / "out")]) == 0


def test_refuses_to_write_phd_application() -> None:
    with TemporaryDirectory() as tmp:
        forbidden = Path(tmp) / "PhD_Application" / "handoffs"
        with pytest.raises(ValueError, match="PhD_Application"):
            write_outputs(build_weekly_handoff(_weekly([])), forbidden)


def test_refuses_to_write_git_directory() -> None:
    with TemporaryDirectory() as tmp:
        forbidden = Path(tmp) / ".git" / "handoffs"
        with pytest.raises(ValueError, match=r"\.git"):
            write_outputs(build_weekly_handoff(_weekly([])), forbidden)


def test_schema_validation_rejects_missing_fields_and_bad_scores() -> None:
    payload = build_weekly_handoff(_weekly([_record("Module-SIS chameleon hash", "Module-SIS.")]))
    missing = json.loads(json.dumps(payload))
    missing["packets"][0].pop("non_claims")
    with pytest.raises(ValueError, match="missing required fields"):
        validate_handoff_payload(missing)

    bad_score = json.loads(json.dumps(payload))
    bad_score["packets"][0]["module_sis_relevance_score"] = 6
    with pytest.raises(ValueError, match="integer from 0 to 5"):
        validate_handoff_payload(bad_score)

    missing_top_level = json.loads(json.dumps(payload))
    missing_top_level.pop("coverage")
    with pytest.raises(ValueError, match="payload is missing required fields"):
        validate_handoff_payload(missing_top_level)

    bad_anchor_type = json.loads(json.dumps(payload))
    bad_anchor_type["packets"][0]["lattice_pqc_anchor_evidence"] = "Module-SIS"
    with pytest.raises(ValueError, match="anchor_evidence must be a list"):
        validate_handoff_payload(bad_anchor_type)


def test_packet_generation_is_deterministic() -> None:
    weekly = _weekly(
        [
            _record("Module-SIS chameleon hash", "Module-SIS."),
            _record("A generic hash", "A generic hash."),
        ]
    )
    assert build_weekly_handoff(weekly) == build_weekly_handoff(weekly)
