# Manual GitHub Publish

This document explains the manual publish path for reviewed repository changes. It does not add automatic push, scheduled sync, or background publishing.

中文说明：本流程只服务人工确认后的 GitHub 发布。它不替代 pull request review，也不会自动同步或强推。

## 1. Manual publish only

Manual-only usage is required.

No scheduled automation is configured. Do not add:

- Windows Task Scheduler integration
- cron jobs
- background service
- startup task
- automatic publish
- automatic runs

The helper script `scripts\manual_publish_to_github.bat` must be double-clicked or run manually. It never installs scheduled tasks and never runs in the background.

## 2. Safety rules

- No automatic push without manual execution.
- No scheduled sync.
- No force push.
- Stop on conflicts.
- Pull/rebase before push.
- Validate before commit.
- Project validation should use `python -m pytest tests` so pytest only collects repository tests and does not recurse into external packages.
- GitHub Actions should remain the validation gate after push.
- Generated artifacts must not be committed unless intentionally handled in a separate artifact publish.

Forbidden artifacts must not be committed:

- `.env`
- `papers.db`
- `state/reading-queue.json`
- `__pycache__/`
- `.pytest_tmp/`
- `exports/`
- `audits/`
- local test `data/*.json`
- local test `digests/*.md`
- real API keys, SMTP passwords, or tokens

## 3. Manual staging model

The recommended helper commits already-staged files only. This avoids broad staging and avoids accidental generated artifacts.

Before running commit mode, manually stage exact reviewed paths. Examples:

```powershell
git status -sb
git diff --check
git add README.md docs/real-manual-quality-pilot.md docs/manual-github-publish.md tests/test_manual_quality_pilot_docs.py scripts/manual_publish_to_github.bat
```

Do not stage generated artifacts. Do not use broad staging for this repository.

## 4. Manual helper

PowerShell:

```powershell
Set-Location "D:\Code\CodexProjects\lattice-crypto-daily-digest"
cmd /c scripts\manual_publish_to_github.bat
```

cmd:

```cmd
cd /d D:\Code\CodexProjects\lattice-crypto-daily-digest
scripts\manual_publish_to_github.bat
```

The helper:

1. verifies the current directory is a Git repository;
2. prints that it does not install scheduled tasks;
3. shows the current branch;
4. fetches origin;
5. pulls with `git pull --rebase origin main`;
6. runs `python -m pytest tests`;
7. runs `python scripts/check_release_hygiene.py`;
8. runs `git diff --check`;
9. shows `git status -sb`;
10. blocks forbidden staged files;
11. asks for a commit message;
12. commits already-staged files;
13. pushes with `git push origin main`.

## 5. Conflict handling

If `git pull --rebase origin main` fails:

- stop;
- do not force push;
- inspect `git status -sb`;
- resolve conflicts manually;
- rerun tests;
- restart the manual helper only after the repository is clean enough.

## 6. After push

After `git push origin main`, GitHub Actions remains the validation gate. If CI fails:

- inspect the failing job;
- avoid force push;
- make a small follow-up fix;
- rerun tests locally before pushing again.

## 7. Pytest collection boundary

Use project-scoped pytest commands:

```powershell
python -m pytest tests
```

Do not rely on bare pytest collection from arbitrary working directories. On Windows, external packages such as pywin32 may include their own tests under global or environment paths; project validation must not collect `site-packages`, `.venv`, `Lib`, `Scripts`, or other external directories.
