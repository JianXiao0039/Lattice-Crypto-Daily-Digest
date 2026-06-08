# Daily Automation Observation Checklist v0.1

## Before Observation

- [ ] 仅在 `D:\Code\CodexProjects\lattice-crypto-daily-digest` 工作
- [ ] 不写入 `PhD_Application`
- [ ] 不写入 `D:\ResearchArtifacts`
- [ ] 不执行 `git add` / `git commit` / `git push` / `git tag`

## Daily Observation Checks

- [ ] `python --version` 符合当前允许环境
- [ ] environment import check 通过
- [ ] `python -m lattice_digest.workflow doctor` 通过
- [ ] `data\YYYY-MM-DD.json` 存在
- [ ] `digests\YYYY-MM-DD.md` 存在或缺失原因明确
- [ ] source health 结果可见
- [ ] `0 records + all-red sources` 时明确标成 source-starved
- [ ] IACR latest 状态可见
- [ ] Semantic Scholar 状态可见，且未打印 key
- [ ] `git status -sb` 已记录

## Post-Observation Interpretation

- [ ] 空日报是否被错误解释为“无论文”
- [ ] source-starved 是否被显式标注
- [ ] 是否需要 manual recovery
- [ ] 是否需要下次再做 live probe
