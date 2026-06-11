# Phase 12X Full Manual Diagnostic Run Log

## Pre-Run State

- Python: 3.15.0b2;
- environment imports: pass;
- doctor: pass;
- package version: 0.3.3;
- worktree: dirty;
- unstaged code: `src/lattice_digest/reliability_dashboard.py`;
- modified generated database: `papers.db`;
- Full Manual Quality Run mode: one-time manual diagnostic only.

## Full Workflow Decision

Command considered:

`python -m lattice_digest.workflow full --execute --generate-notes`

Result: **not executed**.

The command would run a network daily fetch and write daily artifacts, `papers.db`, weekly artifacts, exports, reading queue, Obsidian notes, progress files, and a workflow manifest. Existing dirty code and generated state prevent reliable attribution and create overwrite risk for trusted artifacts.

## Safe Fallback Diagnostic

Command executed:

`python scripts\probe_source_connectivity.py`

Result:

- arXiv: HTTP 200;
- Crossref: HTTP 200;
- DBLP: HTTP 200;
- IACR RSS: HTTP 200, parser success, 100 records;
- OpenAlex: HTTP 200;
- Semantic Scholar: HTTP 429 rate limit;
- Semantic Scholar key: present, length 44; value not printed;
- IACR same-day failed-attempt marker: absent;
- IACR cache XML: absent.

## Interpretation Change

The current probe no longer supports an all-source network outage. Five sources are currently reachable, while Semantic Scholar is rate-limited. This does not alter the Phase 12W historical counts and does not prove that a complete Daily workflow will succeed.

## Generated Files

- Full workflow generated files: none;
- fallback probe persisted files: none;
- `papers.db` changed by Phase 12X diagnostic: no observed change;
- recorded `papers.db` SHA-256: `ECD8FE79C15AC809E41BCEBD7E199948D4962DD674C0C8B3735F5A6B63A84CD2`;
- recorded size: 81920 bytes;
- recorded modification time: 2026-06-10T16:41:05.0497105+08:00.

## CI Evidence

Public GitHub API for HEAD `fce3eae`:

- Ubuntu job: success;
- Windows job: failure;
- authenticated logs: unavailable because `gh` is not authenticated.

## Final Validation

- source budget summary: pass;
- focused tests: 3 passed;
- repository test suite: pass, 452 tests;
- release hygiene: pass for package version 0.3.3 with the existing legacy tracked-artifact warning;
- `git diff --check`: pass;
- no private workspace access or write;
- no ResearchArtifacts write;
- no Git add, commit, push, or tag.
