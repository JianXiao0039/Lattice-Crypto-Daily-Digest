# Source-Starved Triage Checklist v0.1

Status: public operator checklist.

# Use This When

- latest daily digest has 0 records;
- all or most sources are red;
- weekly handoff looks sparse or empty;
- user suspects “empty success”.

# Checklist

- run `python -m lattice_digest.workflow doctor`
- run `python scripts\probe_source_connectivity.py`
- inspect latest daily JSON source health
- inspect whether `source_starved=true` should be applied
- inspect IACR attempt marker and XML cache state
- inspect Semantic Scholar key presence/length only
- decide whether to run bounded manual recovery
- rerun weekly handoff after recovery if weekly artifacts depend on degraded days
- end with `git status -sb`

