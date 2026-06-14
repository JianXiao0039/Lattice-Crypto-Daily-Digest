# Phase 13F Shadow-Mode Controlled Pilot and v0.4.1 Release Recovery

## Executive Summary

Phase 13E dependencies are complete. A controlled manual-only shadow entrypoint now produces a separate audit bundle and passes focused noninterference tests. The pilot is `shadow_mode_ready_with_limits`; v0.5 production remains `blocked_by_multiple_conditions`.

Git evidence contradicts the initial assumption that v0.4.1 was untagged: an annotated tag already exists at `95215b5`. It was not modified. v0.4.1 recovery remains `blocked_by_multiple_conditions` because current CI fails on both platforms, no durable Daily evidence exists, and the generated-artifact allowlist correction is not in origin/main or the tag target.

## Dependency Status

All required Phase 13E reports, track reviews, gate documents, and scripts were present.

## Shadow-Mode Pilot

- Status: `shadow_mode_ready_with_limits`.
- Command: `python scripts\run_v0_5_shadow_mode_pilot.py`.
- Output: `audits/shadow/v0_5_controlled_pilot/`.
- Records: 67; agreements: 30; disagreements: 37; human gold: 0.
- Outputs: manifest, predictions, disagreements, and summary.
- No accuracy claim is made.

## Production Noninterference

The entrypoint rejects production output directories, has no production or ARS runtime imports, is absent from workflows and package code, and writes no production artifacts. Tests hash `papers.db`, data, digests, and handoffs before and after execution.

## Release Recovery

- Active package version: 0.4.1.
- Existing v0.4.1 tag: `95215b5`, immutable in this phase.
- Latest CI: run `27486242311`, Ubuntu and Windows failed at `Run tests`.
- Latest scheduled Daily: run `27458195293`, failed at tests before generation.
- Durable Daily evidence: none.
- Allowlist fix: unstaged locally; absent from HEAD/origin/tag.
- Release decision: `blocked_by_multiple_conditions`.

## ARS Role

ARS experiment-agent and academic-paper-reviewer guidance was used inline for protocol and overstatement review only. ARS did not label papers, run retrieval, modify production code, or become a dependency.

## Gates

- Paper-radar core: stable with release warnings.
- Shadow mode: `shadow_mode_ready_with_limits`.
- v0.5 production: `blocked_by_multiple_conditions`.
- v0.4.1 recovery: `blocked_by_multiple_conditions`.

## Validation Results

- Python: 3.15.0b2.
- Workflow doctor: pass.
- Local v0.4.1 verifier: local checks pass; external gates remain blocked.
- Focused shadow-mode tests: 14 passed.
- Full repository helper: 521 passed.
- Release hygiene: pass with the non-blocking legacy tracked-generated warning.
- `git diff --check`: pass.
- `git diff --cached --check`: pass.
- Current GitHub CI: failed on Ubuntu and Windows at `Run tests`.

## TODO_VERIFY

- Exact failing test logs for current GitHub Actions.
- User adjudication and held-out shadow evaluation.
- Publication of the narrow artifact contract.
- First origin-persisted Daily artifact pair after recovery.
