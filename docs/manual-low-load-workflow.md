# Manual Low-Load Workflow Profiles

本项目不配置任何自动后台任务。Phase 8K 只增加手动触发的低负载 workflow profile，用于笔记本、本地 Windows 环境或临时网络较差时安全运行。

## 1. 明确不做的事情

- No Windows Task Scheduler integration.
- No cron jobs.
- No startup tasks.
- No background services.
- No background daemons.
- No automatic scheduled runs.

所有命令都必须由用户手动触发。默认行为仍是 dry-run，不写文件。

## 2. Profile 类型

### normal

默认 profile。适合正常手动运行：

```powershell
python -m lattice_digest.workflow weekly
```

### low-load

低负载 profile，推荐在笔记本或不想让本地机器长时间跑任务时使用：

```powershell
python -m lattice_digest.workflow daily --low-load
python -m lattice_digest.workflow weekly --low-load
```

在 daily workflow 中，如果用户没有显式指定 `--since`，低负载 profile 会把 workflow 默认的 `7d` 日报窗口收敛到 `36h`，减少运行时间和网络压力。它只在显式传入 `--low-load` 时生效，不改变普通模式语义。

### offline / no-network

离线或无网络 profile 会跳过 daily 抓取步骤，只允许读取已有本地 JSON、阅读队列、source health ledger 和研究产物：

```powershell
python -m lattice_digest.workflow daily --no-network
python -m lattice_digest.workflow full --no-network
```

这不会运行 fetcher，也不会发起网络请求。weekly workflow 本身只使用已有本地文件。

## 3. 写文件仍需要 --execute

下面命令只规划步骤，不写文件：

```powershell
python -m lattice_digest.workflow weekly --low-load
```

下面命令才会写 weekly synthesis、reading queue、artifact export 和 research progress：

```powershell
python -m lattice_digest.workflow weekly --low-load --execute
```

## 4. Obsidian 笔记仍需显式确认

即使使用 `weekly --execute`，Obsidian paper note scaffold 也默认 dry-run。

需要真实生成笔记时必须显式加：

```powershell
python -m lattice_digest.workflow weekly --execute --generate-notes
```

不想看到笔记步骤时可以：

```powershell
python -m lattice_digest.workflow weekly --execute --skip-notes
```

## 5. 可选跳过项

- `--skip-progress`：跳过 advisor update / progress log 生成。
- `--skip-zotero`：research artifact export 不生成 Zotero-oriented pack format。
- `--skip-heavy-sources`：仅作为 workflow-level 低负载提示，不改变 fetcher 语义。
- `--offline` / `--no-network`：跳过 network-dependent daily digest step。

## 6. 推荐手动命令

低负载周工作流 dry-run：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow weekly --low-load
```

低负载周工作流执行：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow weekly --low-load --execute
```

离线查看状态：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow status
```

离线环境检查：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.workflow doctor
```

## English Summary

Manual low-load workflow profiles keep the project user-triggered and resource-aware. The command center does not install scheduled automation, cron jobs, startup tasks, background services, or daemons. Writing workflows still default to dry-run and require `--execute`; Obsidian note generation additionally requires `--generate-notes`. Use `--low-load` for laptop-friendly manual runs and `--offline` or `--no-network` to skip network-dependent daily fetching.
