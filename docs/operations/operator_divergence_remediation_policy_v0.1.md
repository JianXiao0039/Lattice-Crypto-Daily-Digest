# Operator Divergence Remediation Policy v0.1

Status: `operator_divergence_policy_ready`.

If operator outputs diverge, classify the divergence before trusting fallback use.

## Boundary Violation

Examples:

- private path access;
- `git add`, `git commit`, `git push`, or `git tag`;
- background automation;
- release tag operations;
- source/ranking/taxonomy changes.

Action:

- stop trusting that operator for fallback use;
- document the violation;
- require a stricter prompt header;
- require Codex review before future use.

## Command Divergence

Examples:

- different working directory;
- omitted pre-run checks;
- invented unsupported commands;
- skipped source-health probe without reporting.

Action:

- update the operator prompt;
- require the common task set;
- rerun only the divergent task if safe.

## Artifact Divergence

Examples:

- missing Daily/Weekly/Monthly path;
- invalid JSON;
- source-starved status omitted;
- reading queue or Obsidian export omitted.

Action:

- run durable verifier;
- compare paths against the command matrix;
- require Codex review if generated output will be used as evidence.

## Interpretation Divergence

Examples:

- arXiv 429 not classified as rate_limited;
- DBLP TLS/SSL treated as generic failure;
- IACR failed/0 interpreted as no relevant papers;
- Semantic Scholar missing key, auth, rate limit, timeout, and network errors conflated;
- OpenAlex empty response treated as network failure without evidence.

Action:

- update source-health interpretation notes;
- rerun low-load probe later if needed;
- do not claim source health is green unless evidence supports it.

