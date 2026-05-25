# lattice-crypto-daily-digest

## 项目功能

这是一个格密码论文每日雷达。它每天抓取近 24-36 小时新增或更新的格密码相关论文，过滤非密码学 lattice / SIS 噪声，去重后按 A/B/C/D 分类，并输出：

- `digests/YYYY-MM-DD.md`
- `data/YYYY-MM-DD.json`
- `papers.db`

Markdown 日报使用中文输出。即使当天没有 A/B/C 论文，也会生成空日报，而不是伪造推荐。

## 云端自动运行：GitHub Actions

`.github/workflows/daily.yml` 会每天 `01:17 UTC` 自动运行，约等于北京时间/新加坡时间 `09:17 Asia`。也可以在 GitHub 仓库的 `Actions` 页面手动点击 `Run workflow` 运行。

云端流程会安装依赖、运行 `python -m pytest`、生成 Markdown/JSON 日报、更新 `papers.db`，然后只把 `digests/`、`data/` 和 `papers.db` 自动提交回仓库。邮件发送依赖 SMTP secrets；如果 secrets 不完整，只跳过邮件，不影响日报生成和 commit。

OpenAlex、Semantic Scholar、arXiv 等数据源出现 429、SSL、超时或网络 warning 时，不等于失败。项目会记录 warning，并尽量使用其他成功数据源继续生成日报。

## GitHub Secrets 配置

邮件发送需要在 GitHub 仓库中配置 secrets。路径是：

`Settings -> Secrets and variables -> Actions -> New repository secret`

需要配置：

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `DIGEST_EMAIL_TO`
- `DIGEST_EMAIL_FROM`

`SMTP_PASSWORD` 应使用邮箱授权码或应用密码，而不是明文登录密码。不要把真实 SMTP 密码、GitHub token、API key 写入仓库或 `.env.example`。

可选数据源配置：

- `CONTACT_EMAIL`
- `SEMANTIC_SCHOLAR_API_KEY`

## 本地运行

本地验证和生成日报可以直接运行：

```powershell
python -m pytest
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

如需发送本地邮件，先设置 `SMTP_HOST`、`SMTP_PORT`、`SMTP_USERNAME`、`SMTP_PASSWORD`、`DIGEST_EMAIL_FROM`、`DIGEST_EMAIL_TO`，再运行：

```powershell
python scripts/send_latest_digest_email.py
```

邮件脚本只读取最新的 `digests/YYYY-MM-DD.md` 正文，不会发送 `.env`、`papers.db` 或其他敏感文件内容。

## 本地手动补交到 GitHub

如果 Codex 自动化或本地命令已经生成了历史日报产物，可以双击：

```cmd
scripts\push_all_digest_outputs.bat
```

这个 bat 只做本地补交：

- 不抓取论文
- 不运行分类
- 不运行测试
- 只提交 `digests/`、`data/` 和 `papers.db`
- 可一次补交多个历史日期

如果本地 push 失败，先检查 Clash、git proxy 和 GitHub 凭据：

```powershell
git config --global --get http.proxy
git config --global --get https.proxy
git ls-remote https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git
git push
```

之前可用代理示例是 `http://127.0.0.1:7897`，但脚本不会强制修改你的全局代理配置。

## 不推荐 watcher 自启动

不推荐为本项目配置本地 watcher、自启动脚本或 Windows Task Scheduler 计划任务。本地 watcher 依赖电脑持续开机、本地网络、代理、GitHub 登录状态以及 Codex sandbox 对 `.git` 的写入权限，可能带来少量资源占用和权限问题。

推荐使用 GitHub Actions 做云端每日定时运行；本地只保留 `scripts\push_all_digest_outputs.bat`，用于手动补交已经生成好的 `digests/`、`data/` 和 `papers.db`。

## 常见问题

**GitHub Actions 成功但没有邮件怎么办？**  
检查 `SMTP_HOST`、`SMTP_PORT`、`SMTP_USERNAME`、`SMTP_PASSWORD`、`DIGEST_EMAIL_TO`、`DIGEST_EMAIL_FROM` 是否都已配置。SMTP secrets 不完整时，workflow 会输出 `Email sending skipped: SMTP secrets not configured.` 并继续成功。

**GitHub Actions 有 Node.js 20 warning 是否失败？**  
当前这是 warning，不影响日报成功。后续可以升级 actions 版本或设置 Node 24 兼容，但不需要为了 warning 改动业务逻辑。

**本地 push 失败怎么办？**  
检查 Clash 是否运行、git proxy 是否正确、GitHub 凭据是否可用。可以先运行 `git ls-remote https://github.com/JianXiao0039/Lattice-Crypto-Daily-Digest.git` 验证连接。

**看到 429 warning 是否说明日报失败？**  
不是。429 warning 通常表示数据源限流，项目会降级处理并继续使用其他成功数据源；这不等于失败。

**本地 Codex 无法写 `.git` 怎么办？**  
使用 `scripts\push_all_digest_outputs.bat` 手动补交已经生成的日报产物。这个方案不依赖 Codex 直接写 `.git`。
