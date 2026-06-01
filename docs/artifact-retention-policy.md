# Artifact Retention Policy

本策略说明哪些文件适合提交，哪些文件默认只保留在本地。项目是 manual-only workflow；no scheduled automation is configured。No automatic cleanup daemon or scheduled cleanup is recommended.

## 1. Principles

- 功能代码、测试、文档、配置 schema 可以提交。
- 运行产物默认不提交。
- 日报产物只在明确发布或回填时单独提交。
- 密钥永远不提交。
- dry-run 是默认安全模式。
- low-load mode 是笔记本和低资源场景的推荐手动模式。

## 2. Usually committed

- `src/`
- `tests/`
- `docs/`
- `scripts/` 中的手动脚本
- `.github/workflows/`
- `.gitignore`
- `pyproject.toml`
- `README.md`
- `CHANGELOG.md`
- release docs

## 3. Usually not committed

Generated artifacts must not be committed by default. 默认不要提交：

- `exports/`
- `audits/`
- `research_artifacts/`
- `.pytest_tmp/`
- `__pycache__/`
- `state/reading-queue.json`
- `data/*.json`
- `data/weekly/`
- `digests/*.md`
- `digests/weekly/`
- `papers.db`
- `.env`
- cache/log/tmp files

## 4. Digest artifacts

`data/YYYY-MM-DD.json`、`digests/YYYY-MM-DD.md` 和 `papers.db` 可以作为正式日报产物提交，但应满足：

1. 不是本地测试临时生成物；
2. 与功能代码提交分开；
3. 已确认没有密钥或本地绝对路径；
4. `python -m pytest` 通过；
5. source health warning 不代表失败，但需要保留诊断信息。

## 5. Audits and exports

以下目录默认本地保留：

- `audits/source-health/`
- `audits/backfill/`
- `exports/library/`
- `exports/research-artifacts/`
- `exports/research-progress/`
- `exports/obsidian-paper-notes/`
- `exports/workflow-runs/`

这些文件适合本地研究工作流和人工审计，不适合混入代码 commit。

## 6. Reading queue

`state/reading-queue.json` 包含人工阅读状态、review status、Obsidian note path、Zotero key 等 local personal state，默认不提交。reading queue manual statuses should be preserved.

备份建议见 `docs/recovery-playbook.md`。

## 7. Retention cleanup

PowerShell dry-run 清理检查：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
git clean -ndX
```

确认后清理 ignored artifacts：

```powershell
git clean -fdX
```

不要清理未忽略文件，除非已经确认它们不是用户手写资料。不要配置自动清理 daemon、scheduled cleanup、startup cleanup 或后台清理服务。

## 8. English summary

Generated artifacts must not be committed by default. Keep code, tests, docs, and manual scripts in normal commits. Commit `data/`, `digests/`, and `papers.db` only when intentionally publishing digest artifacts. Never commit `.env`, API keys, SMTP passwords, Zotero tokens, caches, temporary files, or local reading queue state.
