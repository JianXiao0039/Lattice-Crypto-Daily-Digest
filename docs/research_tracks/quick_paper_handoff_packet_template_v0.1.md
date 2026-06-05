# Quick-Paper Handoff Packet Template v0.1

Status: reusable public packet template.

Copy this template for a reviewed candidate. Keep all unresolved technical content under `TODO_VERIFY`.

```yaml
packet_id: QPH-YYYY-Www-NN
source_item_title: TODO
source_file: TODO
source_url_or_identifier: TODO_VERIFY
lattice_pqc_anchor_evidence: TODO
category: direct | construction-adjacent | parameterization | implementation | bridge | comparison | background
why_it_matters: TODO
intended_artifact_use: TODO
possible_paper_section: Introduction | Related Work | Preliminaries | Construction | Security Model | Parameterization | Implementation | Comparison | Limitations/Future Work
verified_facts:
  - TODO
TODO_VERIFY:
  - TODO
non_claims:
  - This packet is not a security proof.
  - This packet is not a novelty claim.
recommended_action: handoff_now | handoff_after_verify | keep_in_radar | backlog | exclude
target_artifact_file: TODO
risk_level: low | medium | high
```

# Packet Review Checklist

- [ ] Source title is observed, not invented.
- [ ] Source URL / identifier is trustworthy or marked `TODO_VERIFY`.
- [ ] Lattice/PQC anchor is explicit.
- [ ] Generic keywords are not the only evidence.
- [ ] Intended artifact use names a real task.
- [ ] Possible paper section is named.
- [ ] Verified facts are separated from background and inference.
- [ ] TODO_VERIFY is complete enough for manual reading.
- [ ] Non-claims cover security, novelty, construction, parameters, and implementation where relevant.
- [ ] Recommended action follows the decision rubric.
- [ ] Target artifact file or queue is named.
- [ ] No private PhD application material is included.

# Artifact Intake Record

Fill this only after the artifact workspace reviews the packet.

```yaml
intake_status: accepted | accepted_with_todo | deferred | rejected
intake_date: TODO
artifact_task: TODO
artifact_owner: manual
remaining_todo_verify:
  - TODO
rejection_reason: TODO
```

# Example Exclusion Packet

```yaml
packet_id: QPH-EXAMPLE-EXCLUDE
source_item_title: Generic commitment paper
source_file: TODO
source_url_or_identifier: TODO_VERIFY
lattice_pqc_anchor_evidence: not detected
category: background
why_it_matters: No concrete Module-SIS artifact use was identified.
intended_artifact_use: none
possible_paper_section: none
verified_facts:
  - The title contains the word commitment.
TODO_VERIFY:
  - Whether any lattice/PQC anchor exists.
non_claims:
  - The item is not treated as lattice/PQC relevant.
recommended_action: exclude
target_artifact_file: none
risk_level: low
```

