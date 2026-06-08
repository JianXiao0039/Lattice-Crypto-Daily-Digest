# Source Health Regression Check v0.1

## Summary

本检查区分两层：

1. 持久化 daily artifact / audit；
2. 当前 live probe。

不要把“源当前可达”与“当前日报产物已经刷新为全绿”混为一谈。

## Per-Source Check

| Source | Baseline | Current Observation | Regression Class | Manual Action |
| --- | --- | --- | --- | --- |
| `arxiv` | `green` | direct probe `200` | `unchanged` | 无 |
| `crossref` | `green` | direct probe `200` | `unchanged` | 无 |
| `dblp` | `yellow` | direct probe `200`，artifact 仍 `yellow` | `improved / artifact-unchanged` | 观察下一次 daily 产物 |
| `iacr_eprint` | `yellow` | direct probe `parsed/100`，audit=`cache_hit/100` | `unchanged` | 无 |
| `openalex` | `yellow` | direct probe `200`，artifact 仍 `yellow` | `improved / artifact-unchanged` | 观察下一次 daily 产物 |
| `semantic_scholar` | `yellow` | standalone probe `200`，live dashboard=`rate_limit` | `TODO_VERIFY` | 手动重试，避免过度解释 |

## IACR Latest

- baseline：`fetched/100`
- current artifact：`fetched/100`
- current audit：`cache_hit/100`
- current probe：`parsed/100`
- verdict：未见回归

## Semantic Scholar

- key：`present=true`
- safe length：`44`
- artifact：`no_candidates_to_enrich`
- live dashboard：`rate_limit`
- verdict：富化链路不稳定，但不是明确 auth/network hard failure
