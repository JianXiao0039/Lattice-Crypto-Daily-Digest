# Weekly Public Synthesis Quality Policy v0.1

Status: public weekly-module quality policy.

# Purpose

Define expected behavior for the Weekly Public Synthesis Run.

# Required Behavior

The weekly module should:

1. use current weekly artifacts;
2. generate track-based synthesis;
3. run weekly handoff generation through the supported repository command or script;
4. label output conservatively when weekly input is source-starved or partly source-starved;
5. avoid overinterpreting empty or sparse weekly records;
6. not modify private or ResearchArtifacts workspaces;
7. not commit or push automatically.

# Recommended Commands

```powershell
python -m lattice_digest.workflow weekly --low-load --skip-hygiene
scripts\run_weekly_handoff.bat
git status -sb
```

# Source-Starved Rule

If weekly input depends on several all-red daily runs, the weekly report and handoff should be treated as incomplete coverage, not complete absence of relevant papers.

