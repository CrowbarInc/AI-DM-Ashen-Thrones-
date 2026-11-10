# FAILURE INJECTION

Injected unavailable provider, timeout, FAIL, REVIEW_REQUIRED, VALIDATION_ERROR, malformed/empty candidate, authoritative resolution failure, campaign initialization failure, error object metadata, response serialization failure, unexpected nested/future fields, public-looking objects, session mismatch, disabled/enabled gates, session/campaign reload and malformed request/import.

Recoverable narration failures retain the exact mandatory discovery. Authoritative/serialization failures return safe errors; a serialization failure may occur after state commit and is not a client-delivery acknowledgement. No provider retry or duplicate resolution was added. Optional absent fields have safe defaults; unknown fields fail closed. See failure_injection.json, supplemental_http.json, holdout_results.json and development.xml for the scope actually executed.
