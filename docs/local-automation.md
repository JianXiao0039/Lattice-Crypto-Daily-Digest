# 本地自动化与权威回填

## 采集器角色

GitHub Actions 是 provisional collector：它每天按 UTC 01:17 定时运行，负责在你不开电脑时生成占位日报。GitHub runner 的网络环境可能遇到 arXiv、OpenAlex、Semantic Scholar 的 429、SSL 或 timeout，因此这类报告标记为 `collector=github_actions`、`quality_status=provisional`。

本地 Codex 是 authoritative collector：你恢复使用 Windows / Clash / Codex 环境后，可以用本地网络重新采集指定日期窗口，并把报告标记为 `collector=local_codex`、`quality_status=authoritative_backfill`。

## 每天本地运行

日常本地生成当天报告：

```powershell
python -m lattice_digest.run --since 36h --output markdown,json --send none --collector local_codex --quality-status authoritative --run-mode daily
```

如果已经生成了当天 authoritative 报告，默认不会覆盖；确认要重跑时加 `--force`。

## 三五天后回填

最近 5 天权威回填：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\run_local_digest_backfill.ps1 -Days 5
```

指定日期范围回填：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\run_local_digest_backfill.ps1 -FromDate 2026-05-25 -ToDate 2026-05-29
```

脚本会逐日调用：

```powershell
python -m lattice_digest.run --target-date YYYY-MM-DD --since 7d --output markdown,json --send none --collector local_codex --quality-status authoritative_backfill --run-mode backfill
```

## 为什么不能只用 `--since 7d` 写当天文件

只运行 `--since 7d` 且不指定 `--target-date`，只会把所有结果写入今天的 `data/YYYY-MM-DD.json` 和 `digests/YYYY-MM-DD.md`。这无法替换过去几天由 GitHub Actions 生成的 provisional 日报。backfill 必须逐日指定 `--target-date`，让每一天都有自己的权威报告文件。

## 覆盖策略

- provisional 可以被 authoritative_backfill 覆盖。
- authoritative 或 authoritative_backfill 默认不会被覆盖。
- 确认要覆盖本地权威报告时，给脚本或 run 命令传入 `-Force` / `--force`。
- JSON metadata 的 `supersedes` 会记录被替换报告的 collector、run_date 和 quality_status。

## papers.db 与 backfill

backfill 只在单份报告内部做 dedup。`papers.db` 用于记录最新归档状态，不作为过滤器阻止某篇已出现论文进入某个 target_date 的日报。这样即使论文已经在数据库中存在，本地回填某天时仍能写入该天报告。

## 提交与推送

`scripts\run_local_digest_backfill.ps1` 只暂存：

- `data/*.json`
- `digests/*.md`
- `papers.db`

提交信息格式为：

```text
backfill lattice digest: YYYY-MM-DD..YYYY-MM-DD
```

如果 push 失败，先检查 GitHub 网络、Clash 代理和认证状态。

## Backfill quality audit

本地回填不仅要覆盖 GitHub Actions 的 provisional 日报，还需要知道“本地到底补全了什么”。因此当 `authoritative_backfill` 准备覆盖已有 `collector=github_actions` 或 `quality_status=provisional` 的报告时，旧版本会先保存到：

- `archive/provisional/YYYY-MM-DD.json`
- `archive/provisional/YYYY-MM-DD.md`

新的本地权威版本仍写入：

- `data/YYYY-MM-DD.json`
- `digests/YYYY-MM-DD.md`

审计单日：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\audit_backfill_quality.ps1 -Date 2026-05-29
```

审计日期范围：

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\audit_backfill_quality.ps1 -FromDate 2026-05-25 -ToDate 2026-05-29
```

审计输出：

- `audits/backfill/YYYY-MM-DD.json`
- `audits/backfill/YYYY-MM-DD.md`

`added_by_backfill` 表示本地权威回填比 GitHub provisional 多发现的论文，尤其要关注其中的“必须精读 / 建议精读”。`missing_from_backfill` 表示 GitHub provisional 有、但本地回填没有的论文；这些不能直接丢弃，应该作为风险项人工检查，常见原因包括 API 限流、时间窗口差异、dedup/filter 差异。

可以较放心替换 provisional 的情况：

- 本地 authoritative 论文数更多；
- 本地新增高优先级论文；
- 本地 source health 绿色数据源更多；
- GitHub provisional 有 red source，而本地至少 yellow/green；
- 没有高优先级论文从本地回填中消失。

需要人工检查的情况：

- `missing_from_backfill` 非空；
- GitHub 独有论文里有“必须精读 / 建议精读”；
- 本地 source health 更差；
- 本地总记录数明显少于 GitHub provisional；
- 没有找到 provisional 快照，只能做 authoritative 自检。
