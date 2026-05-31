# Reading Queue Workflow

## 中文说明

`reading_queue` 是本地阅读队列与 review 状态跟踪器。它只读取已有的 weekly synthesis、daily JSON 或 research artifact export manifest，不运行 fetcher，不重新打分，也不改变日报、周报、source health、Zotero export 或 artifact export 的语义。

默认本地状态文件：

```text
state/reading-queue.json
```

该文件是个人本地状态，默认不应提交。

## 1. 导入候选论文

PowerShell：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.reading_queue import --days 7
```

Dry-run：

```powershell
python -m lattice_digest.reading_queue import --days 7 --dry-run
```

指定 weekly JSON：

```powershell
python -m lattice_digest.reading_queue import --weekly-json data\weekly\2026-W22.json
```

导入时会优先读取 weekly synthesis JSON；如果不存在，则使用 daily JSON fallback。导入规则是确定性的：

- A 类且命中主研究板块：`HIGH`
- B 类且命中主研究板块：`MEDIUM`
- 其他候选：`LOW`
- D 类默认不导入，除非明确出现在 `Paper Plan Candidates`

## 2. 查看队列

```powershell
python -m lattice_digest.reading_queue list
```

## 3. 标记阅读状态

允许的 `reading_status`：

- `TODO_READ`
- `TODO_SKIM`
- `READING`
- `SKIMMED`
- `READ`
- `IGNORED`

示例：

```powershell
python -m lattice_digest.reading_queue mark --key arxiv:2605.00001 --reading-status READING
```

允许的 `review_status`：

- `TODO_VERIFY`
- `VERIFIED`
- `NEEDS_REPLICATION`
- `NEEDS_MATH_CHECK`
- `NEEDS_CODE_CHECK`
- `NOT_RELEVANT`

示例：

```powershell
python -m lattice_digest.reading_queue mark --key doi:10.1000/module-sis --review-status NEEDS_MATH_CHECK
```

`mark` 只更新指定状态字段、`updated_at` 和 `status_history`，不会修改标题、来源、分数等无关字段。

## 4. 绑定 Zotero 与 Obsidian

```powershell
python -m lattice_digest.reading_queue link --key arxiv:2605.00001 --zotero-key ABC123 --obsidian-note "Papers\Transformer LWE.md"
```

该命令只记录本地关联，不会写入真实 Zotero library。

## 5. 导出 Obsidian Dashboard

```powershell
python -m lattice_digest.reading_queue export-obsidian
```

输出目录：

```text
exports/reading-queue/
```

生成文件：

- `reading-dashboard.md`
- `todo-read.md`
- `needs-replication.md`

这些是本地生成物，默认不要提交。

## 6. 审计队列

```powershell
python -m lattice_digest.reading_queue audit
```

严格模式：

```powershell
python -m lattice_digest.reading_queue audit --strict
```

审计会检查：

- 非法 reading/review status
- 重复 dedup key
- 缺标题
- 缺 URL
- 缺 seen_dates

严格模式下，如果存在关键错误，会返回非零退出码。

## English Summary

`lattice_digest.reading_queue` is a local reading queue and review-status tracker. It imports deterministic candidates from existing weekly synthesis JSON, daily digest JSON fallback, or research artifact export manifests. It preserves manual reading status, review status, Zotero keys, and Obsidian note links across re-imports.

It does not fetch papers, rerank papers, modify daily/weekly digest semantics, or write to Zotero. Generated local state and Obsidian dashboards are personal runtime artifacts and should not be committed.

Common commands:

```powershell
python -m lattice_digest.reading_queue import --days 7
python -m lattice_digest.reading_queue list
python -m lattice_digest.reading_queue mark --key KEY --reading-status READING
python -m lattice_digest.reading_queue mark --key KEY --review-status NEEDS_REPLICATION
python -m lattice_digest.reading_queue link --key KEY --zotero-key ZKEY --obsidian-note "Papers\paper.md"
python -m lattice_digest.reading_queue export-obsidian
python -m lattice_digest.reading_queue audit --strict
```
