# Reading Queue and Obsidian Export Runbook v0.1

## Reading Queue Export

```powershell
python scripts\export_reading_queue.py --latest
```

Expected outputs:

- `state/reading-queue.json`
- `exports/reading-queue/`

The queue should include reading action, evidence basis, `TODO_VERIFY`, and rationale-derived fields. It must not require manual annotation or human-gold fields.

The reading queue does not require manual annotation to run or export.

Allowed user-facing optional fields are `reading_status` and blank `user_notes` when supported by existing project convention.

## Reading Action Policy

- `精读`: A-class or top monthly/weekly core paper with strong lattice/PQC relevance.
- `扫读`: relevant but less central or useful background.
- `暂存`: peripheral, weak evidence, or possible future relevance.
- `忽略`: weak title-only match, keyword collision, unrelated applied crypto, or low evidence.

Reading action is an explanation layer and does not replace ranking score.

## Obsidian Export

```powershell
python scripts\export_obsidian_notes.py --latest
```

Expected output path inside repository:

- `exports/obsidian-paper-notes/`

Do not write to `D:\ResearchOS` unless the user explicitly authorizes that in a separate task.

## Note Scaffold Requirements

- Front matter defaults to `status: unread`.
- Radar Recommendation.
- Paper Work Summary.
- Relevance to My Research.
- Reading Checklist.
- `TODO_VERIFY`.
- Links.

The scaffold must not claim the user has read the paper.
