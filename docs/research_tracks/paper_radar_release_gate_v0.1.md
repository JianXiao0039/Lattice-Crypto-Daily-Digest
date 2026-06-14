# Paper Radar Release Gate v0.1

## Decision

`radar_core_stable_with_warnings`

The Phase 13E shadow work is isolated from the paper-radar production pipeline. Source ingestion, source health, normalization, ranking, Daily generation, Weekly synthesis, reading queues, handoffs, and production track assignment are unchanged.

## Gate Evidence

| Check | Status | Evidence |
|---|---|---|
| Source ingestion | unchanged | No source implementation changed. |
| Source health | unchanged | No health, retry, or connectivity behavior changed. |
| Daily and Weekly workflows | unchanged | No workflow integration was added. |
| Ranking and production classification | unchanged | Experimental files live under `scripts/`, `experiments/`, and documentation paths. |
| Shadow isolation | pass | Focused tests scan production package and workflows for forbidden imports. |
| Annotation role | review-only | Zero human-gold rows; outputs are not production inputs. |
| Local tests | pass | Required Phase 13E focus: 10 passed; repository helper: 510 passed. |
| Release hygiene | pass with warning | Package 0.4.1 is consistent; legacy tracked-generated warning remains non-blocking. |
| Remote CI | TODO_VERIFY | `gh` is installed but not authenticated in the current environment. |
| Durable-run evidence | still incomplete | Phase 13E does not convert non-persisted runs into durable evidence. |

This gate describes usability of the radar core after isolated shadow work. It does not authorize a v0.4.1 tag or production classifier change.
