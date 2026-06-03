# Semantic Scholar Metadata Enrichment

This document describes the optional Semantic Scholar metadata enrichment layer. It is manual-only and does not create scheduled automation, Windows Task Scheduler tasks, cron jobs, background services, startup tasks, or automatic future runs.

## 1. 目的

Semantic Scholar enrichment 用于对已经进入本项目的论文记录做可选元数据补充，例如：

- `corpusId`
- `paperId`
- `externalIds`
- `url`
- `title`
- `abstract`
- `authors`
- `venue`
- `year`
- `referenceCount`
- `citationCount`
- `influentialCitationCount`
- `openAccessPdf`

它不是 primary paper source，不负责决定论文是否进入日报，也不是 ranking authority。IACR ePrint、arXiv、Crossref、OpenAlex、DBLP 等现有 source ingestion 语义保持不变。

匹配现有 records 时按保守优先级查找：

1. DOI；
2. arXiv ID；
3. Semantic Scholar `CorpusId`；
4. Semantic Scholar `paperId`；
5. exact title fallback。标题 fallback 置信度较低，只用于没有更强 identifier 的记录。

## 2. API key 策略

Semantic Scholar API key 只允许从环境变量 `SEMANTIC_SCHOLAR_API_KEY` 读取。请在本机 shell 或个人 `.env` 中设置真实值，但不要把值写进仓库、文档、issue、日志或截图。

```powershell
# PowerShell: set SEMANTIC_SCHOLAR_API_KEY locally, but do not paste the value into docs or logs.
```

安全规则：

- 不要把 API key 写入代码、测试、文档、报告、README、fixtures、日志或 prompt。
- 不要提交 `.env`。
- 不要在截图、issue、CI 日志或运行输出中暴露 key。
- 请求时 key 只能通过 HTTP header `x-api-key` 发送。
- CI 不需要配置 key；缺少 key 时 enrichment 应该 graceful skip。

## 3. 手动运行方式

PowerShell，在项目根目录运行：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.semantic_scholar_enrichment --input data\2026-06-03.json --dry-run
```

实际生成 enrichment 输出时：

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
python -m lattice_digest.semantic_scholar_enrichment --input data\2026-06-03.json --output-dir exports\semantic-scholar-enrichment --max-requests 20
```

CMD，在项目根目录运行：

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
python -m lattice_digest.semantic_scholar_enrichment --input data\2026-06-03.json --dry-run
```

`exports/semantic-scholar-enrichment/` 是本地生成物，默认不要提交。

## 4. 速率限制与降级

默认策略：

- 每秒最多 1 个请求。
- 每次运行请求数有上限，默认 20。
- 没有 API key 时不请求 Semantic Scholar，只报告 skipped。
- HTTP 429、timeout、5xx、网络错误等失败是 retryable / non-fatal。
- 不做后台轮询，不做自动重试任务，不做定时运行。

## 5. Ranking 边界

Semantic Scholar citation metadata 只作为人工阅读和元数据核验参考：

- `citationCount` 不得直接提高 A/B/C ranking。
- `influentialCitationCount` 不得直接覆盖 reading priority。
- Semantic Scholar enrichment 不改变 taxonomy、negative keywords、query expansion、section classifier 或 ranker thresholds。
- 如果 enrichment metadata 和原始 source metadata 冲突，应标记为 TODO_VERIFY，由人工核验。

## 6. 本地缓存

enrichment 可以写入本地 cache，缓存内容不包含 API key。缓存只保存 sanitized metadata 和 lookup 信息。不要提交 `cache/`。

## 7. 常见问题

### 没有配置 key 会失败吗？

不会。缺少 `SEMANTIC_SCHOLAR_API_KEY` 时，enrichment 会被标记为 skipped，日报、周报、workflow、CI 均应继续运行。

### 为什么 Semantic Scholar 不是 primary source？

因为 Phase 9Q 的结论是 Semantic Scholar 更适合作为 metadata enrichment / cross-source confirmation。核心发现仍优先依赖 source-native latest 或已有 query source，例如 IACR RSS/latest 与 arXiv query groups。

### citationCount 可以用于排序吗？

不可以直接用于 A/B/C ranking。引用数可以作为人工阅读辅助信息，但不能替代格密码相关性、source health、taxonomy 和 ranking explanation。

## English Summary

Semantic Scholar enrichment is optional metadata enrichment for existing digest records. It reads the API key only from `SEMANTIC_SCHOLAR_API_KEY`, sends it only via the `x-api-key` header, and never requires the key for CI or normal digest generation. The enrichment layer is manually triggered, rate-limited to at most one request per second, bounded per run, and non-fatal on failures. Citation metadata is advisory and must not override the project's relevance ranking.
