# V4.2 network authority and availability contract

The release remains fail closed. There is no offline approval reader, signing
key, new trust anchor, skip-provenance switch or automatic quarantine promotion.
No previously authenticated, protected release approval was found on this host.
Plain release receipts, HEAD and origin/main do not authorize offline production.

The six independent observations are local_code_integrity,
release_authorization, remote_freshness, source_retrieval,
scientific_validation and public_upload. Preflight leaves the last three
NOT_ATTEMPTED/NOT_RUN; success does not certify scientific quality or delivery.
LIVE_REMOTE_VERIFIED requires exact local dependency closure, manifest equality,
the existing import/path checks and a fresh real remote main matching HEAD.
The effective origin must equal the compiled approved project HTTPS URL;
changing Git config to a local repository cannot manufacture remote freshness.
On failed live reads the authority mode is AUTHORITY_UNVERIFIED even when local
integrity passes. OFFLINE_CODE_INTEGRITY_VERIFIED is reserved and disabled;
there is no eligible offline candidate acquisition path in this release.

Live provenance uses at most three attempts, each at most three seconds, within
a twelve-second monotonic budget, with 0.2/0.4 second backoff. Git error text is
classified in memory into fixed codes; neither proxy credentials nor arbitrary
stderr is written into the runtime receipt. SHA mismatch and local tampering
are separate from network failure. TLS and authentication failures stop retry.

Only a proxy endpoint failure for the exact reviewed project HTTPS origin may
reuse an already enabled static Windows HTTPS proxy. The proxy must be HTTP(S)
on loopback, with an explicit port, no credentials, query, fragment or path.
PAC configurations are refused. There is no direct-Internet fallback or proxy
installation. Overrides apply only to a Git child process. TLS verification is
forced and GIT_SSL_NO_VERIFY is not inherited. No global Git, Windows, firewall,
certificate or scheduler configuration is changed.

The isolated public publisher can reuse that validated Windows proxy in its
temporary Git repository for this exact origin. Read transport retry is bounded
by sixty seconds in total. Pushes are never blindly retried: the existing
non-force reconciliation, stable event ownership, privacy validation and fresh
remote-byte readback remain mandatory. Network upload failure preserves the
existing verified PUBLISH_PENDING candidate; scientific rejection is not pending
publication. Retry never grants authority or revises canonical source history.

Canonical source collection records actual start/end clocks in its existing
runtime journal. Preflight failure records explicit negative production/delivery
states. UNKNOWN scheduler timestamps stay UNKNOWN; manual recovery cannot prove
scheduled delivery. Existing task IDs, Daily 09:00, Weekly Monday 10:30 and
Monthly first-day 12:00 Asia/Singapore are unchanged. No fourth scheduler exists.

Network restoration does not fix missing scientific evidence. The V4.1 64 MiB
bounded history reader, independent report gate, DOI/arXiv/ePrint ownership and
public catalog conflict rejection remain unchanged. Recovery must preserve the
original pair, exact window and actual retrieval time; authoritative promotion
still requires live preflight and the existing approved repair transaction.

Dependency map: public Daily/Weekly/Monthly and repair/delivery preflights call
runtime_provenance. public_delivery then independently verifies report_gate,
public_report privacy and public_publisher remote read/write/readback.
cloud_daily instead reads cloud_public_history from GitHub and verifies its
public snapshot and independent science gates; its workflow event token never
becomes a local authoritative runtime credential. Cloud failure remains failure.
