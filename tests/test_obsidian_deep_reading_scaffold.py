from __future__ import annotations

from lattice_digest.obsidian_scaffold import render_note


def _record() -> dict[str, object]:
    return {
        "dedup_key": "title:deep-reading-paper",
        "title": "Deep Reading LWE Paper",
        "source": "arxiv",
        "source_url": "https://example.test/lwe",
        "date": "2026-06-20",
        "class_label": "A",
        "relevance_label": "A",
        "relevance_score": 90,
        "score": 90,
        "queue_priority": "HIGH",
        "reading_action": "精读",
        "reading_status": "TODO_READ",
        "review_status": "TODO_VERIFY",
        "research_direction": "LWE / RLWE / MLWE",
        "evidence_basis": ["abstract-derived"],
        "rationale_zh": "从摘要看，论文关注 LWE attack cost.",
        "rationale_en": "The paper addresses LWE attack-cost analysis.",
        "core_novelty_zh": "摘要支持贡献声明；证明和参数仍需核验。",
        "core_novelty_en": "The abstract supports a contribution claim; verify proof and parameters.",
        "radar_relevance_zh": "与格密码/PQC 雷达相关。",
        "radar_relevance_en": "Relevant to the lattice/PQC radar.",
        "TODO_VERIFY": ["TODO_VERIFY: proof details."],
        "todo_verify_categories": ["proof / security model"],
        "status_history": [],
    }


def test_obsidian_scaffold_contains_deep_reading_template_sections() -> None:
    note = render_note(_record())
    for section in [
        "## 0. Radar Decision",
        "## 1. 中文推荐理由",
        "### 论文大致工作",
        "### 核心创新点",
        "### 与本雷达关系",
        "## 2. English Rationale",
        "### Paper work summary",
        "### Core novelty",
        "## 3. Direction Mapping",
        "## 4. Deep Reading Checklist",
        "## 5. Claim Verification",
        "## 6. Research Use",
        "## 7. Links",
    ]:
        assert section in note
    assert "status: unread" in note
    assert 'research_direction: "LWE / RLWE / MLWE"' in note


def test_obsidian_scaffold_has_claim_verification_and_no_hallucinated_read_status() -> None:
    note = render_note(_record())
    assert "| Claim | Evidence in available metadata | Need full-paper verification? | Notes |" in note
    assert "TODO_VERIFY" in note
    assert "has read" not in note.lower()
    assert "already read" not in note.lower()
