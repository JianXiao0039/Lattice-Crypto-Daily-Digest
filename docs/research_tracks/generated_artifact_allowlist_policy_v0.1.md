# Generated Artifact Allowlist Policy v0.1

## Daily Publication Allowlist

- `digests/<validated-digest-date>.md`
- `data/<validated-digest-date>.json`
- existing tracked `papers.db`, staged without force

## Never Allowed by Force-Add

- `digests/*.md` or `data/*.json` globs;
- whole `digests/` or `data/` directories;
- `papers.db` via force-add;
- weekly handoffs, exports, audits, notes, caches, PDFs, HTML, `.env`, or private workspace files.

## Release Hygiene

The allowlist applies only to the explicit Daily publication workflow. It does not weaken `scripts/check_release_hygiene.py` for source/release commits.
