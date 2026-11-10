# FAILURE RECOVERY

Executed: duplicate start, missing/unknown/corrupt/incomplete save IDs, stale active campaign displaced then resumed, repeated and incompatible branch choices/follow-ups after resume, hidden private fields, provider unavailability/timeout, malformed/empty/rejected publication, transient/persistent rename faults, and failed reset rollback. Existing PR37 and PR66 suites supply additional opening/publication faults; exact failures remain reported.

Not fully executed in browser: network loss, refresh DURING initialization, frontend deadline expiry, duplicate physical Start dispatch under a slow provider, interrupted gameplay connection, corrupted active session recovery, and process-crash recovery. File-level retry never reruns consequences. Permanent errors remain errors; rollback can itself fail under a persistent filesystem outage and is not a power-loss transaction guarantee.
