# No Background Automation Policy v0.1

## Policy

Phase 13O runbooks are manual-only. They do not create:

- Windows Task Scheduler tasks;
- cron jobs;
- startup tasks;
- watchers;
- background services;
- automatic future runs;
- hidden browser automation;
- release tags.

## Manual-Only Meaning

An operator may run documented commands in the foreground and report the result. The operator must not install a persistent service, schedule a future job, or configure a watcher.

## Full Run

The full radar run is a command sequence executed by an operator. It is not a one-click automatic pipeline and it does not authorize Git write operations.
