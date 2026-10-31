# 04 — Preflight Verification

preflight verifies requested/effective live mode using the production predicate,
credential presence (boolean only), local SDK installation, actual cached contract
model plus configured default/high-precision/escalation models, relevant execution
flags, fixture-import flag equality, existing safe-store guard, exact match between
fixture snapshot and loaded store, fresh initialized durable accounting, positive
token ceilings, requested admission ceiling (1–2), disabled application retries,
and skipped startup provider probe. Model routing and expression flag are recorded.
Provider reachability is explicitly unprobed. No credential value is serialized.

Pending checks require an existing pending ASK in the active scene, no executed
intention, an existing player character, and scene-local valid NPC choices.
They inspect only; snapshots prove no state change. Store mismatch and stale
fixture values fail before a caller can execute. No generic gameplay fallback.

preflight_valid.json records live requested/effective true, zero admissions and
the selected gpt-4.1-mini model. preflight_failure_*.json preserve failures for mode,
credentials, model, import flags, unsafe store, limits, uninitialized ledger,
missing/stale pending state, invalid actor/targets/scene/status, retries, malformed
token bounds, disabled provider, startup probe and consumed budget. Each test
asserts no callback and unchanged state. Used-budget control correctly reports its
pre-existing admission count of one; it adds none. Disabled mode is separately
verified as requested/effective false, and then restored.

These are local structural readiness assertions, not provider health or semantic
success. Existing durable admission enforcement remains the production owner.
Global accounting source-manifest staleness from R1-02 is still unresolved; no
global preflight PASS is claimed. A future runner must retain SDK retry cap zero,
exclusive process/store/ledger ownership, and invoke guarded_trial immediately
before its actual chat callback. This pass does not upgrade the old runner.
