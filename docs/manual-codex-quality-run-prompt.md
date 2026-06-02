# Manual Codex Quality Run Prompt

This prompt is for manual copy/paste or manual trigger only. Do not put it into a recurring automation.

中文说明：本文档给出“质量优先”的手动 Codex 运行提示词。它只适合用户在需要时手动复制、手动粘贴、手动触发。不要把它放进任何 ChatGPT / Codex recurring automation、watcher、startup task、Windows Task Scheduler、cron、后台服务或自动每日运行。

## 1. Manual-only boundary

Manual-only usage is mandatory.

No scheduled automation is configured. Do not add or enable:

- Windows Task Scheduler
- cron
- startup task
- background service
- watcher
- automatic daily run
- recurring ChatGPT / Codex automation

如果旧的外部 Codex 自动化 prompt 仍在每天运行，请停用它。尤其不要继续运行包含以下陈旧命令的 prompt：

- stale digest command: `python -m lattice_digest.run --since 36h --output markdown,json --send none`
- stale bare pytest command: `python -m pytest`

裸 `python -m pytest` 可能在 Windows 上收集全局 `site-packages` 测试并触发 access violation。

## 2. Quality-first manual generation

Quality-first manual generation is allowed and preferred when the user intentionally wants real digest or research outputs.

quality-first manual generation is allowed when it is manually triggered and reviewed.

Recommended principles:

- 用户手动触发；
- 允许正常网络访问以提高真实内容质量；
- 生成后人工检查 artifacts；
- 发布前运行项目范围测试；
- 不自动提交，不自动推送；
- 不提交 generated artifacts，除非明确进入正式产物发布流程。

Low-load / no-network / dry-run are fallback modes only:

- `--low-load`：笔记本、电池、低负载场景；
- `--no-network` / `--offline`：网络故障、API 限流、诊断场景；
- dry-run：检查计划步骤，不写文件。

## 3. Safe validation commands

Never use bare `python -m pytest`.

Use the repository-local helper:

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
scripts\run_project_tests.bat
```

Or use the explicit project-scoped pytest command:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m pytest tests --basetemp=.pytest_tmp
```

`.pytest_tmp/` is local, ignored, and safe to delete after tests.

## 4. Manual prompt template

Copy this only when you want a manual quality-first run:

```text
请在 D:\Code\CodexProjects\lattice-crypto-daily-digest 中进行一次手动 quality-first 检查。

严格要求：
1. 不要创建 recurring automation。
2. 不要创建 Windows Task Scheduler。
3. 不要创建 cron。
4. 不要创建 startup task。
5. 不要创建 background service。
6. 不要执行 git add、git commit、git push、git tag。
7. 不要使用裸 python -m pytest。
8. 项目测试必须使用 scripts\run_project_tests.bat，或 python -m pytest tests --basetemp=.pytest_tmp。
9. 生成的 data、digests、exports、audits、papers.db、.pytest_tmp 不要提交。

请先运行：
git status -sb
python -m lattice_digest.workflow doctor

如需测试，运行：
scripts\run_project_tests.bat

如需真实内容生成，由我手动确认后再运行 workflow daily 或 weekly 的 --execute 命令。
```

## 5. What not to automate

Do not automate these commands locally:

- `python -m lattice_digest.run --since 36h --output markdown,json --send none`
- `python -m lattice_digest.workflow daily --execute`
- `python -m lattice_digest.workflow weekly --execute --generate-notes`
- `python -m lattice_digest.workflow full --execute --generate-notes`
- `scripts\manual_publish_to_github.bat`
- `scripts\push_all_digest_outputs.bat`

All write-enabled commands should be visible, intentional, and reviewable.
