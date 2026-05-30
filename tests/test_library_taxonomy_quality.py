from __future__ import annotations

import json
from pathlib import Path

from lattice_digest.library_taxonomy import classify_text


FIXTURE = Path(__file__).parent / "fixtures" / "library_taxonomy_cases.json"


def _as_set(value: object) -> set[str]:
    return set(value) if isinstance(value, list) else set()


def test_library_taxonomy_fixture_quality() -> None:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert 40 <= len(cases) <= 60

    for case in cases:
        result = classify_text(title=case["title"], abstract=case["abstract"])
        buckets = {
            "research_tags": set(result.research_tags),
            "lattice_tags": set(result.lattice_tags),
            "pqc_tags": set(result.pqc_tags),
            "attack_tags": set(result.attack_tags),
            "primitive_tags": set(result.primitive_tags),
            "implementation_tags": set(result.implementation_tags),
            "ai_tags": set(result.ai_tags),
            "zotero_tags": set(result.zotero_tags),
            "obsidian_links": set(result.obsidian_links),
        }

        for bucket, expected in case.get("expected_present", {}).items():
            missing = _as_set(expected) - buckets[bucket]
            assert not missing, f"{case['id']} missing {bucket}: {sorted(missing)}; notes={case.get('notes')}"

        for bucket, expected in case.get("expected_absent", {}).items():
            unexpected = _as_set(expected) & buckets[bucket]
            assert not unexpected, f"{case['id']} unexpected {bucket}: {sorted(unexpected)}; notes={case.get('notes')}"
