# Release Gate Blocker Matrix v0.1

| Gate | v0.4.1 | v0.5 RC | Notes |
| --- | --- | --- | --- |
| Tag state | exists, blocked historical tag | no v0.5 tag created | Do not move tags |
| Package version | 0.4.1 | 0.4.1 active package | v0.5 is feature-track RC, not package retag here |
| Local tests | TODO_VERIFY per final validation | green locally after validation | CI still separate |
| Remote CI | unverified / prior failed evidence | unverified | `gh` unauthenticated |
| Durable Daily evidence | missing at tagged commit | representative Daily verified | v0.4.1 remains blocked |
| Weekly/Monthly evidence | not part of tag | verified for RC | v0.5 usability evidence |
| Source health | historical issue | acceptable for RC with explicit degradation | no source-health overclaim |
| Release notes | stale | draft needs CI/v0.4.1 note | update before final release |
| Manual annotation | absent | absent | no blocker |
| Background automation | absent | absent | no blocker |

## Production Gate

`blocked_until_ci_green` for final release publication.

`eligible_for_v0_5_final_release_decision` after CI and release notes are verified.
