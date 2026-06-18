# Phase 13N v0.5 RC Test Log

## Planned Validation

```powershell
python --version
python -m lattice_digest.workflow doctor
python -c "import lattice_digest; print(lattice_digest.__version__)"
python -m py_compile scripts\verify_v0_5_rc.py
python -m pytest tests\test_v0_5_rc_gate.py tests\test_bilingual_rationale_policy.py tests\test_v0_5_paper_radar_usability.py -q --basetemp=.pytest_tmp
python scripts\verify_v0_5_rc.py --date 2026-06-15 --week 2026-W25 --month 2026-06
scripts\run_project_tests.bat
python scripts\check_release_hygiene.py
git diff --check
git status -sb
```

Results are recorded in the final Phase 13N response.
