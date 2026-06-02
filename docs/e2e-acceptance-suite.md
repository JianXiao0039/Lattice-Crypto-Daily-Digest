# End-to-End Workflow Acceptance Suite

## 1. 目的

Phase 9A 的 E2E acceptance suite 用于验证手动、低负载科研工作流是否能在没有网络、没有密钥、没有后台任务的情况下稳定运行。

它不是新的产品功能，也不改变论文抓取、排序、source health、日报、周报、阅读队列、Obsidian scaffold 或 workflow command center 的语义。它只用确定性 fixture 检查已有链路是否仍然互相兼容。

## 2. Fixture 位置

测试数据放在：

```text
tests/fixtures/e2e/
```

当前 fixture 包含：

- `daily-2026-05-25.json`
- `daily-2026-05-26.json`
- `daily-2026-05-27.json`
- `reading-queue-state.json`
- `source-health-2026-05-27.json`

这些 fixture 覆盖：

- LWE / BKZ / AI4Lattice 真阳性；
- Module-SIS / chameleon hash / commitment 真阳性；
- ML-KEM implementation / side-channel 真阳性；
- `Falcon-X` 这类非 PQC Falcon 误报；
- `Practical Anonymous Two-Party GBDT` 这类非 lattice / LWE / SIS / PQC 误报；
- source health 的 green / yellow / red；
- 已手动标注的 reading queue 状态。

## 3. 覆盖的工作流

E2E 测试覆盖以下手动链路：

1. 从 daily JSON 聚合生成 weekly synthesis；
2. 从 weekly JSON 生成 research artifact export pack；
3. reading queue import 保留人工状态；
4. Obsidian paper note scaffold dry-run 不写文件；
5. Obsidian paper note scaffold generate 只写临时目录；
6. research progress 输出 advisor update 和 verification backlog；
7. workflow weekly dry-run 不写文件；
8. workflow weekly `--execute` 在临时目录内只写预期输出；
9. 误报不进入错误研究板块；
10. 不创建 Task Scheduler、cron、watcher 或后台服务文件；
11. 输出排序保持确定性。

## 4. 运行命令

PowerShell：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m pytest tests\test_e2e_workflow_acceptance.py --basetemp=.pytest_tmp
```

cmd：

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
python -m pytest tests\test_e2e_workflow_acceptance.py --basetemp=.pytest_tmp
```

完整验证：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m pytest tests --basetemp=.pytest_tmp
python scripts\check_release_hygiene.py
git diff --check
git status -sb
```

## 5. 安全边界

Acceptance suite 必须保持以下边界：

- 不执行网络请求；
- 不依赖 Zotero；
- 不读取用户密钥；
- 不写真实 `data/`、`digests/`、`exports/`、`state/` 或 `papers.db`；
- 不生成或注册 scheduled task；
- 不新增 cron、watcher、startup、background service；
- 不执行 `git add`、`git commit`、`git push` 或 `git tag`。

测试运行时只使用临时目录。生成的临时文件由 pytest/TemporaryDirectory 清理，不应作为仓库产物提交。

## 6. 误报验收标准

`Falcon-X` fixture 只能作为普通 watchlist / 背景项处理，不得进入：

- `PQC Standards / ML-KEM / ML-DSA / Falcon`

`Practical Anonymous Two-Party GBDT` fixture 可以进入 general privacy 背景，但不得进入：

- `AI-assisted Lattice Cryptanalysis`
- `LWE / RLWE / MLWE`
- `SIS / NTRU / Commitments / Chameleon Hash`
- `PQC Standards / ML-KEM / ML-DSA / Falcon`

这两个样例用于防止研究板块分类因为关键词表面匹配而漂移。

## 7. English Summary

The Phase 9A E2E acceptance suite verifies the manual low-load research workflow with deterministic fixtures. It covers weekly synthesis, research artifact export, reading queue import, Obsidian note scaffolding, research progress export, and workflow weekly dry-run/execute behavior. The suite performs no network requests, requires no secrets, creates no scheduler/cron/background automation, and writes only to temporary directories.

The false-positive fixtures ensure that `Falcon-X` is not treated as the Falcon/FN-DSA post-quantum signature scheme, and that a generic anonymous two-party GBDT paper is not routed into AI4Lattice, LWE, SIS, or PQC sections.
