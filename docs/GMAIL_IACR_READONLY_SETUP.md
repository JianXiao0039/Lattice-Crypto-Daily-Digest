# IACR Gmail read-only integration candidate

This code is an isolated candidate, not an installed collector or a new scheduled task.
The existing Codex Gmail connector was actually queried for the exact IACR sender and
newsletter subject. That authorization does not provision credentials for Python.

`lattice_digest.iacr_mail` provides a text/plain MIME parser, bounded synchronization,
public-source reconciliation, and a GET-only Gmail REST adapter. The Daily entry runs
the optional status stage. Its default provider is absent, so it truthfully reports
GMAIL_AUTHORIZATION_REQUIRED and continues public research collection. There is no
ambient token lookup, credential file, browser-session extraction or hidden OAuth.

Before enabling the local REST provider, an operator must authorize an interactive
Google OAuth flow requesting only `https://www.googleapis.com/auth/gmail.readonly`.
This grant can read the mailbox; it is NOT restricted to the IACR sender. The program
additionally restricts list queries and validates sender/subject again after reading.
The metadata-only scope cannot read bodies. Modify, send, delete and full mail scopes
are prohibited. Consent cannot be replaced by a pasted password/token or cookies.

Store refresh credentials only in an explicitly approved OS-backed vault. Supply an
in-memory access-token callable to `GmailReadonlyAPI`; the caller must handle consent,
refresh and revocation without logging secrets. This candidate deliberately does not
install a new secret store or assume that an existing credential is approved. The
vault-backed factory and interactive consent integration are deployment blockers.

The authorized Daily integration must statically inject that provider and restricted
private checkpoint into `optional_daily_stage`, then accept its proposed checkpoint
only after report QA and durable publication. No credential or checkpoint may live in
the checkout or published runtime. Use a user-only ACL private local directory;
persist derived metadata/IDs/hashes only, never raw mail. The current default Daily
stage does not persist a checkpoint and does not claim automatic mailbox monitoring.

Initial synchronization defaults to 14 disclosed days, four pages of fifty messages,
and a 48-hour overlap. Partial pagination, count mismatch or transport failure does
not advance the successful watermark. Stable message IDs prevent repeat ingestion.
Optional history checks require an explicitly configured newsletter label; otherwise
sender-scoped bounded resynchronization is used. Expired history falls back to that
same bounded query. No daemon, Pub/Sub or fourth automation is needed.

Parsed title/author boundaries are provisional. Wrapped headings cannot always be
distinguished from names using plain text alone. The complete bibliographic lines
are retained privately; matching the same ePrint ID against saved official public
title+authors closes this boundary without scheme/title exceptions. Unmatched mail
stays pending public verification and never becomes a primary research event.

References: [Google scopes](https://developers.google.com/workspace/gmail/api/auth/scopes),
[Gmail synchronization](https://developers.google.com/workspace/gmail/api/guides/sync).
