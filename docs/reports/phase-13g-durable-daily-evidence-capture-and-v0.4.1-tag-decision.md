# Phase 13G Durable Daily Evidence Capture and v0.4.1 Tag Decision

## Executive Summary

Phase 13F dependencies are complete. Active version sources remain 0.4.1, v0.4.0 remains immutable, and the paper-radar core remains unchanged. No durable Daily evidence exists.

The requested tag decision is complicated by an existing local and remote annotated `v0.4.1` tag at `95215b5`. Phase 13G did not create or modify it. Current release status is `blocked_by_multiple_conditions` because CI is red on both platforms and no complete post-tag Daily artifact pair or retained evidence bundle exists in `origin/main`.

## Durable Evidence

- Evidence class: `insufficient_evidence`.
- `HEAD` equals `origin/main` at `57a7b3a`.
- Complete Markdown/JSON pairs from June 12 onward: 0.
- Durable evidence manifests in origin: 0.
- Local June 12/13 files are untracked and lack durable run identity.

## CI Confirmation

Latest run `27486931415` failed at `Run tests` on Ubuntu and Windows. Authenticated logs are unavailable. A clean archive of the exact commit passes all 521 tests locally under Python 3.15.0b2, while CI uses Python 3.11; exact root cause remains `TODO_VERIFY`.

## Whitespace

`git diff --check` and `git diff --cached --check` return exit code 0. Messages are CRLF-to-LF normalization warnings only and are classified `line_ending_warning_only`, not a release blocker.

## Release Gates

- Package version: pass.
- v0.4.0 immutability: pass.
- Local tests: pass.
- Release hygiene: pass with legacy warning.
- True whitespace errors: absent.
- Ubuntu CI: fail.
- Windows CI: fail.
- Durable Daily evidence: fail.
- Core invariant: pass with release warnings.
- Shadow isolation: pass.
- v0.5 production: remains blocked.

Decision: `blocked_by_multiple_conditions`.

## Validation Results

- Python: `3.15.0b2`.
- Workflow doctor: pass; Asia/Singapore is healthy and critical.
- Release candidate verifier: local checks pass; external gates remain blocked.
- Durable evidence verifier: `insufficient_evidence`.
- Focused tests: 7 passed after final verifier hardening.
- Full project tests: 524 passed.
- Release hygiene: pass with the documented non-blocking legacy generated-artifact warning.
- `git diff --check`: exit 0; line-ending warnings only.
- `git diff --cached --check`: exit 0.
- Staged files: none.

## Changes

Phase 13G adds a read-only durability verifier, three focused tests, evidence records, CI confirmation, release gates, and ARS reviews. It does not change production behavior.

## TODO_VERIFY

- Authenticated failed-test logs or Python 3.11 reproduction.
- Publication and exercise of the narrow Daily persistence contract.
- First identifiable, validated, origin-persisted Daily run.
- Historical documentation clarification for the already-existing tag.
