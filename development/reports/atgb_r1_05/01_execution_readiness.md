# 01 — Execution Readiness

ATGB-R1-05, 2026-10-19. Controlled validation; production implementation authority NONE.
HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9. Extensive pre-existing dirty/untracked
work retained. Entry status and hashes are in artifacts/atgb/atgb_r1_05/.

Read Constitution, canonical docs/NEXT_SESSION.md, validation evidence standard,
product-realization validation, review standard and completed R1-01/02/03/04 evidence.
support/docs/NEXT_SESSION.md does not exist in this checkout; prior passes establish
that it is the review-bundle spelling. Used canonical docs/NEXT_SESSION.md.

All 3,996 R1-04 entry hashes match before execution. R1-02 orchestration and R1-04
readiness/control remain present. No material baseline discrepancy or experimental
integration. Frozen frontier-gate-v1 manifest also passes load_baseline verification.
Ten current import/mode safety tests pass (readiness_tests.xml); R1-04's prior
167-test result is preserved historical evidence, not a new full run. No full suite.

Each live trial runs in a new process, new exclusive store and durable ledger.
L1/L2 independently copy the same preserved pre-S08.2 reconstruction: exact S08.1
delivered log, authored scene, world, character and combat, with fresh runtime IDs.
No provider call recreates S08.1. Original intermediate historical session was not
retained: exact experimental equivalence is not claimed. No cross-trial state/cache
or environment mutations. L4 uses readiness.seed_control, clears inherited pending
state and creates pending ASK through production chat with the R1-04 setup stub.
Only the measured revision uses the live model. No tests or R1-03 runner imported.

All three live preflight.json files say ready: requested/effective live true,
provider configured, default/high-precision/escalation model gpt-4.1-mini, matching
import flags and store, zero used admissions, ledger initialized, max two admissions,
positive token caps, application retries disabled, startup probe skipped; L4 pending
checks pass. Experimental planning/candidate flags absent after configuration load.
SDK constructor wrapper enforces max_retries=0 and records each actual client.
No semantic/prompt/model changes. API callable is used directly; HTTP/browser not tested.
Input/output/total token ceilings are 16000/2000/18000 per trial; these are ceilings,
not measured usage or a price budget. No configured price table. Provider reachability
was unprobed before the authorized calls. Global accounting source-manifest staleness
from R1-02 persists; no claim that the global stale-source preflight passes.

One initial external-transfer auto-review rejection prevented process creation.
User explicitly approved the named OpenAI destination, context categories, model
and bounded trials before approved live execution. No rejection bypass occurred.
Two offline payload previews cost zero admissions: first failed closed on isolated_store
and fixture_matches_store because the new runner's ASHEN_DATA_DIR identified its own
store as active player state. Callback never ran; snapshots unchanged. Only the new
runner's binding convention was corrected, then a fresh offline preview passed and
captured the payload. Neither preview is a live trial or trial retry. All evidence retained.
