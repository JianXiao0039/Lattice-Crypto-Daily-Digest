# Release Gate Next Actions v0.1

## Do Not Do in Phase 13P

- Do not run `git add`.
- Do not run `git commit`.
- Do not run `git push`.
- Do not run `git tag`.
- Do not delete, move, recreate, or force-update `v0.4.1`.

## Recommended Next Actions

1. Authenticate GitHub CLI or check GitHub Actions in the UI.
2. Confirm latest Windows and Ubuntu CI results for current `origin/main`.
3. Update release notes to document v0.4.1 as an existing blocked historical tag.
4. Keep v0.4.1 untouched.
5. If CI is green and release notes are clean, prepare a separate v0.5 final release decision.
6. Before any commit phase, review dirty generated files such as `papers.db` separately.

## Suggested Read-Only Commands

```powershell
git status -sb
git log --oneline -10
git show --stat --oneline v0.4.1
python scripts\verify_v0_5_rc.py --date 2026-06-15 --week 2026-W25 --month 2026-06
python scripts\verify_durable_artifacts.py --date 2026-06-15 --week 2026-W25 --month 2026-06
python scripts\check_release_hygiene.py
git diff --check
```

GitHub Actions, if authenticated:

```powershell
gh run list --limit 10
```
