# Failure handling

Fault injection, no live calls. Each required case deterministically resolves the
notice-board clue, withholds the candidate, publishes action-focused fallback,
and accepts another action. Full traces: failure_injection_assessed.json and
quarantine_evidence. RuntimeError retains existing VALIDATION_ERROR diagnostics;
timeout records provider_timeout. Both errors are recorded, not successful AI.

| Case | Diagnostic | Marker | Continuation HTTP | Result |
|---|---|---|---:|---|
| provider_unavailable | VALIDATION_ERROR | None | 200 | PASS |
| provider_timeout | provider_timeout | None | 200 | PASS |
| empty | VALIDATION_ERROR | None | 200 | PASS |
| malformed | VALIDATION_ERROR | None | 200 | PASS |
| validation_fail | FAIL | None | 200 | PASS |
| review_required | REVIEW_REQUIRED | None | 200 | PASS |
| validation_error | VALIDATION_ERROR | None | 200 | PASS |
| unauthorized_inventory | FAIL | None | 200 | PASS |
| unauthorized_persistent | FAIL | None | 200 | PASS |
| missing_discovery | REVIEW_REQUIRED | None | 200 | PASS |
| take_key | None | None | 200 | PASS |

All ten required cases PASS. Malformed narration supplies validation-error
recovery; focused PR57 tests additionally inject validator exceptions/decisions.
Take-key is an extra unsupported-action boundary, not a discovery action. No
inventory was added; it correctly differs from a notice-board discovery control.

Fresh fixture NPCs can initialize from absent to runtime defaults. All required
fault post-action authority matches the ordinary no-provider discovery control,
including NPC initialization, clocks and world state. Before/after hash equality
would be an incorrect state-integrity requirement here.
