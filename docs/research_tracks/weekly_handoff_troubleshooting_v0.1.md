# Weekly Handoff Troubleshooting v0.1

Status: public manual troubleshooting guide.

# Missing Weekly JSON

Symptom:

```text
No weekly JSON files found under data\weekly
```

Actions:

1. Confirm an existing weekly JSON is present.
2. Use a specific path:

```powershell
python -m lattice_digest.weekly_handoff --weekly-json data\weekly\YYYY-Www.json --dry-run
```

The generator does not fetch or create weekly input automatically.

# Empty Records

An empty weekly input is valid.

Expected result:

- valid JSON;
- empty `packets`;
- empty `excluded`;
- source-health caveat;
- Markdown stating no handoff packets were generated.

# All Records Excluded as Noise

This can be correct when no record has a sufficiently specific lattice/PQC anchor and artifact use.

Review:

- title/abstract metadata;
- taxonomy and keyword evidence;
- original paper;
- hard-anchor policy.

Do not weaken the generic keyword exclusion merely to produce candidates.

# Unexpected Module-SIS Candidates

Broad weekly section membership is not hard evidence.

Review:

- explicit title/abstract evidence;
- tags/taxonomy evidence;
- ranking explanation;
- whether the packet is only `handoff_after_verify`.

Keep metadata-only candidates TODO_VERIFY.

# Xingye Bridge Candidate Looks Like a Verified Fact

Every public bridge packet must:

- use `xingye_lu_bridge`;
- remain `handoff_after_verify` at metadata level;
- include `no professor-specific fact is asserted`;
- include the mandatory PI-topic non-claim.

If these are missing, do not use the packet.

# Output Path Refused

The generator refuses output paths containing:

- `PhD_Application`;
- `.git`.

Use the default ignored public path:

```powershell
python -m lattice_digest.weekly_handoff --latest --output-dir handoffs\weekly
```

# No Network Requirement

The generator reads local JSON only and requires no network or API key.

It must not:

- fetch papers;
- call Semantic Scholar;
- use `SEMANTIC_SCHOLAR_API_KEY`;
- write secrets.

# Python Dependency Check

Run:

```powershell
python --version
python -c "import pytest, pydantic; from zoneinfo import ZoneInfo; print('env ok'); print(ZoneInfo('Asia/Singapore'))"
```

# Pytest Scope

Use repository-scoped tests and local basetemp:

```powershell
python -m pytest tests\test_weekly_handoff.py --basetemp=.pytest_tmp
scripts\run_project_tests.bat
```

Do not run bare `python -m pytest`.

# Schema Validation Failure

Possible causes:

- missing required field;
- duplicate handoff ID;
- unsupported track/action;
- score outside 0–5;
- missing mandatory non-claim.

Regenerate from a valid weekly JSON. Do not manually delete non-claims to force output.

# Generated Outputs and Git

`handoffs/` is ignored and should not be committed by default.

Check:

```powershell
git status -sb --ignored handoffs
```

# Private and Cross-Workspace Boundaries

- Never write handoff outputs into `PhD_Application`.
- ResearchArtifacts synchronization remains manual and is not implemented by this generator.
- Never write into `.git`.
- No scheduler or background service is configured.

