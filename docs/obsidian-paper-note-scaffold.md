# Obsidian Paper Note Scaffold

## 中文说明

Phase 8H 增加 `lattice_digest.obsidian_scaffold`，用于从本地阅读队列 `state/reading-queue.json` 生成 Obsidian 兼容的论文笔记骨架。它只读取 Phase 8G 的 reading queue 状态，不抓取论文、不重新排序、不改变日报或周报输出、不写入 Zotero。

默认输出目录：

```text
exports/obsidian-paper-notes/Papers/
```

该目录是本地生成物，默认不要提交。

## 1. 基本命令

PowerShell：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.obsidian_scaffold generate
```

dry-run：

```powershell
python -m lattice_digest.obsidian_scaffold generate --dry-run
```

指定真实 Obsidian vault：

```powershell
python -m lattice_digest.obsidian_scaffold generate --vault-dir "D:\ObsidianVault" --papers-subdir Papers
```

## 2. 默认筛选规则

默认只为以下记录生成 scaffold：

- `reading_status` 属于 `TODO_READ,READING`
- `review_status` 属于 `TODO_VERIFY,NEEDS_MATH_CHECK,NEEDS_REPLICATION,NEEDS_CODE_CHECK`
- `queue_priority` 属于 `HIGH,MEDIUM`

默认跳过：

- `reading_status = IGNORED`
- `review_status = NOT_RELEVANT`

## 3. 自定义筛选

```powershell
python -m lattice_digest.obsidian_scaffold generate --statuses TODO_READ,READING --review-statuses TODO_VERIFY,NEEDS_REPLICATION --priorities HIGH
```

## 4. 生成内容

每个 paper note 包含 YAML frontmatter 和固定章节：

- Metadata
- Why Queued
- Reading Goal
- TL;DR
- Core Problem
- Method / Construction / Attack Idea
- Mathematical Checkpoints
- Experiment / Artifact Checkpoints
- Relation to My Research
- Possible Use
- Questions for Advisor
- Reading Log
- Verification Status

生成内容使用保守占位符，例如 `TODO_AFTER_READING`、`TODO_VERIFY`、`Needs verification`。脚本不会编造摘要、贡献、攻击结论、安全证明或实验结果。

## 5. 已有笔记处理

默认不覆盖已有文件。如果目标文件已经存在，脚本会跳过并报告。dry-run 不写任何文件。

## 6. 回写 reading queue

如果使用 `--update-queue`，脚本会把生成或已存在的 note path 写回 `obsidian_note_path`，并追加 `status_history` 记录。

```powershell
python -m lattice_digest.obsidian_scaffold generate --update-queue
```

该操作不会改变 `reading_status`、`review_status`、`zotero_key` 或其他人工字段。

## English Summary

`lattice_digest.obsidian_scaffold` generates deterministic Obsidian-compatible paper note skeletons from the local reading queue. It does not fetch papers, rerank records, modify daily/weekly digest generation, or write to Zotero.

Common commands:

```powershell
python -m lattice_digest.obsidian_scaffold generate
python -m lattice_digest.obsidian_scaffold generate --dry-run
python -m lattice_digest.obsidian_scaffold generate --vault-dir "D:\ObsidianVault" --papers-subdir Papers
python -m lattice_digest.obsidian_scaffold generate --update-queue
```

Generated notes are local runtime artifacts and should not be committed unless the user explicitly decides to publish them.
