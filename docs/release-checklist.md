# Release Checklist

## 中文说明

## 1. Pre-release checks

在发布前运行：

```powershell
git status -sb
python -m pytest
git diff --check
```

确认：

- README deployment sections present.
- `.env.example` present.
- no generated artifacts accidentally staged.
- no secrets.
- no `.pytest_tmp`.
- no `papers.db` unless intentional.
- no `data/*.json` or `digests/*.md` unless intentionally publishing digest artifacts.
- `CHANGELOG.md` includes the release entry.
- `docs/releases/v0.1.0.md` exists.
- License status is clear. If no license has been chosen, keep `TODO: choose license`.

## 2. Smoke tests

只在准备发布时运行；不要把 smoke-test 产物混入功能 commit。

36h run:

```powershell
python -m lattice_digest.run --since 36h --output markdown,json --send none
```

7d run:

```powershell
python -m lattice_digest.run --since 7d --output markdown,json --send none
```

Weekly brief generation:

```powershell
# TODO: add command when a public weekly brief entry point exists.
```

Obsidian export if command exists:

```powershell
# TODO: add command when a public single-paper Obsidian export entry point exists.
```

Idea Bank smoke test:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_idea_bank.ps1 -DryRun
```

Paper Plan smoke test:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\generate_paper_plans.ps1 -DryRun
```

## 3. Git release commands

以下命令仅供人工发布时参考。本文件只是文档，不自动执行。

```powershell
git fetch origin
git pull --rebase origin main
git add README.md .env.example CHANGELOG.md docs tests scripts
git commit -m "Prepare v0.1.0 release"
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin main
git push origin v0.1.0
```

## v0.2.0-rc1 Release Candidate Checklist

v0.2.0-rc1 是 Library Interoperability Release Candidate，不是 stable v0.2.0。发布前检查：

- VERSION or package version updated.
- CHANGELOG updated.
- `docs/releases/v0.2.0-rc1.md` exists.
- README links to v0.2.0-rc1.
- `docs/library-interop.md` exists.
- `scripts/export_library.ps1` exists.
- `schemas/library-item.schema.json` exists.
- `tests/test_library_export.py` passes.
- `python -m pytest` passes.
- export dry-run passes.
- actual export passes.
- `exports/library/` cleaned before commit.
- no `data/*.json` accidentally staged.
- no `digests/*.md` accidentally staged.
- no `papers.db` accidentally staged.
- no `.pytest_tmp` staged.
- no secrets.

Documentation-only release commands; do not execute automatically:

```powershell
git fetch origin
git pull --rebase origin main
git add pyproject.toml src/lattice_digest/__init__.py CHANGELOG.md README.md docs tests schemas scripts src/lattice_digest/export_library.py src/lattice_digest/library_taxonomy.py
git commit -m "Prepare v0.2.0-rc1 release"
git tag -a v0.2.0-rc1 -m "Release v0.2.0-rc1"
git push origin main
git push origin v0.2.0-rc1
```

## 4. Rollback notes

Delete local tag:

```powershell
git tag -d v0.1.0
```

Delete remote tag:

```powershell
git push origin :refs/tags/v0.1.0
```

Revert release commit if necessary:

```powershell
git revert <release-commit-sha>
git push origin main
```

## 5. GitHub Release body template

```markdown
# Lattice Crypto Daily Digest v0.1.0

First public research automation release for lattice cryptography paper intelligence.

## Highlights

- Daily lattice crypto digest.
- Source Health red/yellow/green diagnostics.
- Local authoritative backfill.
- GitHub Actions provisional digest.
- Idea Bank, Paper Plan, and Research Artifact scaffold.
- Public deployment guide.

## Known limitations

- External APIs may rate-limit.
- Semantic Scholar works best with API key.
- GitHub Actions coverage can be weaker than local runs.
- This tool is research triage, not a formal bibliographic database.

## Validation

- `python -m pytest`
- `powershell.exe -ExecutionPolicy Bypass -File scripts\check_deployment.ps1`
```

## English summary

Use this checklist before tagging a public release. Verify tests, deployment documentation, secrets hygiene, generated artifact boundaries, release notes, and rollback commands. Do not stage generated digest outputs unless the release intentionally publishes them.
