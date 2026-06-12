# Phase 13A ARS Evidence Review

## Review Scope

This review applies the `academic-research-suite` academic-paper-reviewer methodology and devil's-advocate perspectives to the Phase 13A main report, durable-run evidence log, and tag decision. It is a read-only claim and reproducibility review. Repository tests, release hygiene, Git history, and GitHub Actions remain the authoritative engineering evidence.

## Material Passport

| Item | Status | Use |
|---|---|---|
| Phase 13A main report | ANALYZED | Release-readiness claims |
| Durable post-tag evidence log | ANALYZED | Run classification and persistence evidence |
| v0.4.1 tag decision | ANALYZED | Gate consistency |
| GitHub Actions API metadata | ANALYZED | Current and historical CI status |
| GitHub Actions failed-step logs | NOT_AVAILABLE | Exact CI stderr cannot be verified because `gh` is unauthenticated and the public log endpoint is unavailable |
| ARS external review/runtime | NOT_USED | Cross-model review, hooks, full runtime, and agent-team mode remained disabled |

## Methodology Review

### Evidence Strengths

1. Run `27327344162` is classified as `non_persisted_automation_post_tag_actual`, not durable evidence. Generation success is not conflated with Git or origin persistence.
2. The selected submission contract is narrow and auditable: only the verified date-specific Markdown and JSON paths may use force-add. `papers.db`, broad directories, caches, exports, notes, and private paths are excluded.
3. Local working-tree validation, current origin CI, and historical CI are reported separately.
4. The release decision remains blocked until both current CI and a durable post-tag run satisfy the documented gate.

### Reproducibility Gaps

1. The new generated-artifact contract has focused local tests but has not yet completed an automation run that persists both artifacts to `origin/main` with traceable CI.
2. No run currently satisfies every durable-evidence field: retained Markdown and JSON, source-health record, validation, Git persistence, origin persistence, CI traceability, and unambiguous run type.
3. Current failed GitHub Actions jobs expose step status but not failed-command stderr in the available evidence. Exact CI failure text remains `TODO_VERIFY`.
4. The local release verifier demonstrates repository-state consistency only. It cannot establish remote CI green status or create durable automation evidence.

## Devil's Advocate Review

### Major Finding: Release Readiness Must Not Be Inferred from Local Success

The strongest counterargument to a ready/stable claim is that the only observed post-tag Daily executions are non-persisted, while current Ubuntu and Windows jobs for the active origin commit are red. Local tests can validate the proposed patch but cannot substitute for an origin run.

Required wording: use "local validation passed" only after final commands pass. Do not use "release ready", "automation stable", or "durable evidence obtained" in Phase 13A.

### Major Finding: Submission Root Cause Has Two Evidence Levels

The ignored-path conflict is directly supported by `.gitignore` and the previous broad `git add` command. The exact remote stderr is unavailable. The report may state that the repository contract explains the persistence failure, but must mark the unavailable failed-step log as a limitation.

### Moderate Finding: CI Asymmetry Is Historical, Not Current

Historical run `27388260673` had both platforms green. Current runs for later commits have both platforms red. Therefore "Ubuntu passes, Windows fails" is not an accurate current-state summary unless tied to a specific historical run. Phase 13A should report current both-red status and historical both-green evidence separately.

### Moderate Finding: Stability Claims Have Zero Durable Samples

There are zero durable automation post-tag Daily runs and zero actual post-tag Weekly automation runs. Reliability and stability claims are unsupported. The valid conclusion is that the protocol and contract are prepared for the next evidence-producing run.

## Editorial Synthesis

Decision: **major evidence revision / release blocked**.

The Phase 13A documents are appropriately conservative if they retain these statements:

* durable Daily evidence count is zero;
* the generated-artifact allowlist is implemented but not yet proven by an origin-persisted automation run;
* current GitHub Actions evidence is red on both platforms for the active origin commit;
* v0.4.1 tag decision is `blocked_by_multiple_conditions`;
* v0.5 offline precision design may continue, while production classification changes remain blocked.

## Required Follow-Up Evidence

1. Run the patched Daily workflow from an origin commit and retain its run identifier.
2. Verify the exact target-date Markdown and JSON are committed and present in `origin/main`.
3. Link source-health and validation evidence to the same run.
4. Obtain green Ubuntu and Windows CI for the candidate commit, or document an explicitly approved platform exception.
5. Re-run the release verifier and tag checklist only after the remote evidence exists.

## Claim Review Verdict

* Evidence overstatement: avoided if the blocked decision remains unchanged.
* Automation/manual confusion: avoided; classifications are distinct.
* Reproducibility: protocol sufficient for the next run, evidence incomplete today.
* Release stability claim: unsupported and must not be made.
* Tag recommendation: `blocked_by_multiple_conditions`.

