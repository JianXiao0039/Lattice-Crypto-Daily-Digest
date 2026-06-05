# Quick-Paper Handoff Protocol v0.1

Status: public protocol for transferring actionable radar findings to the Module-SIS chameleon hash artifact workspace.

# Purpose

Transfer evidence, questions, and concrete tasks from:

`D:\Code\CodexProjects\lattice-crypto-daily-digest`

to:

`D:\ResearchArtifacts\module-sis-chameleon-hash`

without turning the radar repository into the proof, implementation, or paper-construction repository.

# Boundary Rules

- Radar repo owns discovery, classification, source evidence, TODO_VERIFY, exclusion, and packet drafts.
- Artifact workspace owns construction feasibility, proof skeleton, parameterization, implementation, tests, and comparison tables.
- `D:\Code\CodexProjects\PhD_Application` is private and must never receive or supply files through this public protocol.
- A handoff never changes ranking, taxonomy, source ingestion, or workflow semantics.

# Eligible Handoff Categories

1. Direct Module-SIS / SIS / lattice chameleon hash.
2. Construction-adjacent lattice commitments, trapdoors, signatures, or privacy primitives.
3. Parameterization and estimator support.
4. Implementation and reproducibility support.
5. Public Xingye Lu technical bridge item with verified lattice/PQC anchor.
6. Comparison-table baseline.

# Required Evidence

Every packet must include:

- source title or track item;
- public source file;
- source URL / identifier when available;
- lattice/PQC anchor evidence;
- intended artifact use;
- possible paper section;
- verified facts;
- TODO_VERIFY;
- non-claims;
- recommended action;
- target artifact file;
- risk level.

# Decision Flow

1. Does the item have a clear lattice/PQC/SIS/Module-SIS anchor?
   - No: `exclude`.
2. Can it support a named artifact task or paper section?
   - No: `keep_in_radar` or `backlog`.
3. Are the required paper facts and technical relation verified?
   - No: `handoff_after_verify`.
4. Is overclaim risk controlled with explicit non-claims?
   - No: keep in TODO_VERIFY.
5. Otherwise:
   - `handoff_now`.

# Intake Destinations

| Intended use | Suggested artifact destination |
| --- | --- |
| related work | `paper/related_work.md` or research-radar queue |
| construction question | construction feasibility matrix |
| proof obligation | proof skeleton / security model notes |
| parameter input | parameterization checklist |
| implementation method | implementation plan / tests |
| comparison dimension | comparison table |

# Weekly Integration

Weekly track reports should identify:

- direct handoff candidates;
- TODO_VERIFY candidates;
- backlog;
- excluded noise;
- next original-paper / ChatGPT web reading candidates.

The weekly relevance score is discovery context, not a handoff decision by itself.

# Non-Claims

- Handoff is not proof.
- Handoff is not novelty.
- Handoff is not a working construction.
- Handoff is not a security parameter recommendation.
- Handoff is not an implementation result.
- Handoff is not private application material.

# Manual-Only Rule

This protocol is manual. It creates no scheduler, cron job, Task Scheduler task, startup task, daemon, or background service.

