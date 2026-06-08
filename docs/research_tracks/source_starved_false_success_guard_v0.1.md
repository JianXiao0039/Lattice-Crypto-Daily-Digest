# Source-Starved False-Success Guard v0.1

Status: public guardrail doc.

# Core Rule

- `0 records + all-red sources = source-starved`

# What Source-Starved Means

- source-starved is not a successful paper-discovery result
- empty daily digest under source-starved input is not evidence of no relevant papers
- empty weekly handoff under source-starved input is not evidence of no handoff candidates

# Operational Rule

- recovery should be manual
- do not create automatic retry loops
- do not create background services
- do not schedule retries outside the existing automation UI

# Reporting Rule

Future runs should explicitly say:

- whether the run is source-starved
- why it is source-starved
- what manual recovery path is recommended
