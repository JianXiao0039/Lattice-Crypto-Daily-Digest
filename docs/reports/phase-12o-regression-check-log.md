# Phase 12O Regression Check Log

生成日期：2026-06-08

## Commands Run

```powershell
python --version
python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print('pytest ok'); print('pydantic ok'); print(ZoneInfo('Asia/Singapore'))"
python -m lattice_digest.workflow doctor
python scripts\print_current_reliability_baseline.py
python scripts\daily_reliability_dashboard.py --skip-probe --format json
python scripts\probe_source_connectivity.py
python scripts\daily_reliability_dashboard.py --format json
cmd /c scripts\run_weekly_handoff.bat
python scripts\compare_reliability_baseline.py
python scripts\compare_reliability_baseline.py --with-probe --format json
python -m pytest tests\test_compare_reliability_baseline.py --basetemp=.pytest_tmp -q
```

## Key Runtime Observations

- baseline printer：artifact-only，指标与 Phase 12N freeze 一致。
- daily dashboard `--skip-probe`：与冻结基线一致；`generated_artifacts_present=true`。
- direct probe：
  - 六个源均有一次 `reachable=true` 记录；
  - Semantic Scholar key 仅以 `present=true, length=44` 方式暴露；
  - IACR RSS/latest 可达且解析出 `100` 条。
- live dashboard：
  - `source_reachability_rate=0.833`
  - `semantic_scholar_enrichment_status=rate_limit`
  - 说明 live probe 存在瞬时不稳定。
- weekly handoff：
  - `week=2026-W23`
  - `packets=20`
  - 输出文件仍为 `handoffs\weekly\2026-W23-handoff-packets.json/.md`

## Observation Verdict

- artifact baseline comparison：`unchanged`
- live source observation：存在 `Semantic Scholar rate_limit`，其余源可达
- source-starved：`false`
- false-success guard：本轮未触发且未失效
- automation UI v0.3 prompt 是否已实际生效：`TODO_VERIFY`
