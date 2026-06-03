# Phase 10G Dual-Track Workflow Boundary

This is a public boundary note for the research tooling repository.

## Purpose

This repository remains the public research tooling track for lattice cryptography paper intelligence. It should contain reusable tooling, public documentation, tests, and non-private research workflow notes.

Private PhD application materials must stay outside this repository.

## Folder Boundary

### Public research tooling track

Path:

`D:\Code\CodexProjects\lattice-crypto-daily-digest`

Appropriate public content:

- source code for lattice/PQC digest tooling
- public deployment and troubleshooting docs
- public release notes
- generic workflow documentation
- tests and fixtures that do not contain private application material
- public-safe research tooling reports

### Private application track

Path:

`D:\Code\CodexProjects\PhD_Application`

Private content must remain local:

- PhD narratives
- SoP drafts
- target PI notes
- cold email drafts
- advisor-specific pitches
- application tracker
- personal self-assessment
- funding or program matching notes
- sensitive application planning

## Public-to-Private Direction

Public tooling outputs may be used as inputs for private planning when manually copied or summarized by the user.

Examples of public-safe inputs:

- paper titles
- public metadata
- digest summaries
- reading queue summaries
- generic idea summaries
- public research workflow reports

## Private-to-Public Restriction

Do not copy private application materials back into this repository.

Do not add:

- target PI email content
- SoP text
- personal PhD narrative
- application tracker entries
- recommendation strategy
- personal self-assessment
- funding strategy
- private advisor-specific positioning

## Manual-Only Policy

No scheduled automation is configured here.

Do not add:

- Windows Task Scheduler tasks
- cron jobs
- background services
- startup tasks
- automatic application-material generation

All workflow steps should remain manually triggered.

## Secret and Privacy Policy

Do not commit:

- `.env`
- API keys
- SMTP passwords
- tokens
- private application materials
- private PI notes

Only mention environment variable names when needed, never secret values.

## Validation Boundary

When validating this public repository, use project-scoped tests and repository-local temp isolation as documented elsewhere in the project.

This note does not introduce new code, new automation, or new scheduled behavior.
