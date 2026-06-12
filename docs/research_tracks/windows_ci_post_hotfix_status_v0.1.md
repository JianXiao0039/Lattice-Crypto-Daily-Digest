# Windows CI Post-Hotfix Status v0.1

Status: `TODO_VERIFY after publication`.

- Historical Windows-only failure existed at run `27336481022`.
- Later runs `27391048701` and `27399295488` fail on both platforms because origin/main lacks the complete local corrective patch.
- A clean HEAD archive reproduces portable-path and release-document failures.
- Current local Windows tests validate the corrective working tree, not remote CI.

Do not claim Windows CI green until a run on the published patch succeeds.
