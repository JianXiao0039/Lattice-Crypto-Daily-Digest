# Phase 12Y: Version and Tag Consistency Audit

## Executive Summary

The `v0.4.0` tag exists and points to commit `08c5f07967739ecd008773c4b167cd736848df88`, timestamped `2026-06-11T01:05:06+08:00`. Package metadata at that commit and at current HEAD reports `0.3.3`.

Verdict: `inconsistent_requires_followup`.

## Audit Table

| Check | Result |
|---|---|
| `v0.4.0` exists | yes |
| Tag target | `08c5f07967739ecd008773c4b167cd736848df88` |
| Tag kind | lightweight commit tag |
| `pyproject.toml` version at tag | `0.3.3` |
| package `__version__` at tag | `0.3.3` |
| current package version | `0.3.3` |
| release documentation | available through v0.3.3 |
| public GitHub Release v0.4.0 | not found through public API |
| intentional tag-only policy documented | not found |

## Interpretation

The repository has a v0.4.0 tag without matching package metadata or a located v0.4.0 release note. This may be a tag-only operational milestone, but that intent is not documented in the inspected evidence.

No version or tag was changed in Phase 12Y. A later, separately approved release task should either document the tag-only convention or align release metadata without rewriting the existing tag.

## TODO_VERIFY

- Whether a GitHub Release was created privately or later removed.
- Whether maintainers intentionally separated repository tag version from package version.
- Whether v0.5 planning should first close this release-accounting gap.
