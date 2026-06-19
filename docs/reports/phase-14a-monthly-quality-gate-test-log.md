# Phase 14A Monthly Quality Gate Test Log

## Focused Validation

Commands:

```powershell
python -m py_compile scripts\audit_monthly_rationale_quality.py
python -m pytest tests\test_monthly_rationale_quality_audit.py tests\test_monthly_keyword_only_regression.py tests\test_monthly_quality_gate_policy.py tests\test_monthly_audit_no_manual_annotation.py -q --basetemp=.pytest_tmp
python scripts\audit_monthly_rationale_quality.py --latest
```

Results:

- py_compile: passed.
- focused tests: 11 passed.
- real monthly audit: `pass_with_limits`, score 79.

## Coverage

The tests cover:

- synthetic good monthly artifact;
- keyword-only top-paper rationale;
- missing TODO_VERIFY;
- missing evidence basis;
- conclusion claim without conclusion evidence;
- weak relevance overpromotion;
- bilingual rationale acceptance;
- no manual annotation dependency;
- deterministic output;
- latest-month selection.
