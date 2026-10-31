# ATGB-03B — Provider accounting integrity

Date: 2026-10-18. Status: IMPLEMENTED AND DETERMINISTICALLY VALIDATED; CURRENT-SOURCE ACCOUNTING READINESS VERIFIED; REVIEW PENDING. No live-provider benchmark or real API request was executed. No conversational improvement is claimed.

## Root cause and correction

The ATGB-03A failure investigation identified an infrastructure implementation defect: the existing budget checked a completion counter before dispatch, but incremented it only after completion. Concurrent admissions could share the final allowance. A dispatch interrupted before `finish_request` could disappear. The contract interpreter bypassed the owner entirely; planner/candidate adapters recorded successful returns but not dispatch exceptions. Narration could also report a second completion when parsing failed after the provider response was already accounted. Host performance counters had a narrower scope than provider usage and were absent on the S04.2 early return.

`game/provider_budget.py` remains the single accounting authority. Version `ATGB-03B-1` adds explicit request-attempt identities and an atomic admission/dispatch/completion lifecycle. No competing gameplay or semantic authority was created. Extending this owner carries the needed behavior without architectural restructuring.

Admission now checks the existing request/token ceilings under its existing lock, reserves one application request and pending input/output allowance, and writes an `admitted` event with flush/fsync before returning permission. The count includes admitted attempts that never reach dispatch. This conservative upper bound is intentionally distinct from observed dispatched/completed requests. The next request cannot consume the same final allowance. Pending token reservations prevent concurrent requests from sharing estimated token allowance.

`RequestAttempt.dispatch` writes a durable `dispatch_attempted` event before invoking the original SDK callable once. It catches `BaseException`, writes failure/interruption completion evidence, and rethrows to the owner's existing exception policy. Successful response usage is accounted before caller parsing, so partial/malformed text cannot erase the attempt. A second completion observation returns the same record and does not increment counters/tokens again. A second dispatch or duplicate admission identity is refused. No new retry is introduced.

Unknown, incomplete, inconsistent, or negative token telemetry remains unknown; snapshot totals are null after unknown usage and while a dispatched request is unfinished. The existing conservative stop on unavailable provider usage is retained. Failed durable admission/dispatch writes prevent dispatch. Completion-write failure stops further admissions and does not apply token accounting twice if another layer observes that failure. A durable pending admission remains evidence even when no completion can be written.

Active accounting requires a fresh writable ledger path. Exclusive creation prevents a new process from resetting counters over an existing ledger, including an interrupted one. No resume/replay of old accounting state is silently attempted. Accounting remains opt-in through the existing request-limit/usage-path variables; ATGB sets both before importing the game API. Ordinary inactive accounting adds no ledger writes. Provider-disable gates still prevent dispatch.

## Complete application dispatch inventory

The production entry point starts the game API. Seven application SDK dispatch owners were found. Their eligibility conditions differ; a source reference is not evidence that it executed. `dispatch_inventory.json` records owner, purpose, prior guard/ledger, admission, dispatch, completion, exceptions, conditions, and coverage for every owner.

| Owner | Purpose and eligibility | Before repair |
| --- | --- | --- |
| `api_upstream_preflight.run_upstream_api_preflight` | Startup/explicit health probe; startup obeys `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT` | No budget or ledger coverage |
| `gm.call_gpt` | Existing routed narration, primary/OOC and retry purposes; existing provider/retry gates | Guard with completion counting; duplicate completion possible after parser failure |
| `live_chat_interpretation.request_interpretation` | Production interpretation when enabled and provider calls permitted | Guard plus completion/failure records; no admission reservation |
| `expressive_dialogue.request_expression` | Existing expression eligibility and expression/provider disable gates | Guard plus completion/failure records; some host counts omit expression |
| `semantic_interpreter._invoke_interpretation_model` | Contract interpretation when enabled and production interpretation not already consumed | No budget or ledger coverage |
| `unified_semantic_planning._invoke_provider` | Existing unified-planner flag and planner selection | Guard; successful-return records only |
| `host_constrained_candidates.invoke_candidate_provider` | Existing unified-planner and candidate-selection flags | Guard; successful-return records only |

All seven now use explicit admission plus `attempt.dispatch`. Existing owner fallback/propagation, model selection, prompts, schema, sampling, timeout, output cap, and SDK retry settings stay unchanged. Feature-gate functions and interpretation precedence are unchanged. Tests directly exercise conditional owners using stubs without asserting those owners were active in the original trial.

Separate experiment runners and developer qualification clients also contain provider calls. They are explicitly inventoried as non-runtime utilities and are not certified by ATGB's application readiness. Production imports interpretation schema/prompt/adapter helpers, not those runners; their existing import behavior was inspected. This repair does not claim a global budget for independently launched development experiments.

## Identity, durable evidence, and compatibility

Each active attempt has a local stable `attempt_id`, process `run_id`, version, purpose, owning dispatch function, configured model, admission time, dispatch status, and completion status. Provider response IDs remain a separate `request_id`; provider/model identity, latency, usage and generic error status are retained when available. No API credentials, prompts, request bodies, response text, or provider exception message is written by this accounting layer.

The durable JSONL now contains versioned initialization/admission/dispatch/completion events. Consumers must filter event types; counting every row is incorrect. Completed rows retain `sent`, `purpose`, provider `request_id`, model and usage fields. `snapshot.records` remains completion-only; `snapshot.events` exposes lifecycle evidence. `snapshot.requests` now means consumed admissions, not completed sent requests. `request_upper_bound`, dispatched/pending counters, and explicit unknown tokens separate these concepts. Legacy `begin_request`/`finish_request` entry points remain compatibility observers; all production dispatch owners use explicit attempt objects.

Historical ATGB-03 records are untouched and remain completion-only observations. The new implementation does not retroactively prove their completeness, fill S04.2 telemetry, invent a remaining allowance, or certify a same-trial resume.

## S04.2 early return and ATGB reconciliation

`game/api.py:_live_interpretation_block_response` now attaches the existing `_performance_record` without changing reply text, resolution kind, mutation decisions, or log behavior. Only available latency/usage is supplied; unavailable token fields remain null. Separate metadata labels the accounting bound as **process-cumulative admissions**, avoiding a false per-turn interpretation. Original S04.2 evidence remains byte-identical.

ATGB's readiness check no longer unconditionally refuses or succeeds. It verifies the exact reviewed application-source fingerprints, accounting-owner fingerprint, seven dispatch-function AST fingerprints, and that SDK references pass through `attempt.dispatch`. Missing manifests, changed implementations, new/unwrapped dispatch sites, new HTTP-client modules, or changed application sources fail closed. The manifest is not regenerated during execution. Revisions require review and updated validation. Static evidence is supplemented by controlled tests of every owner; it is not a general proof about arbitrary future code or third-party SDK internals.

ATGB initializes accounting before API startup, reconciles durable lifecycle events with the owner snapshot before/after turns, and uses admissions for request enforcement. Host telemetry is preserved independently. Expression-only requests and missing host performance no longer force a fabricated zero or an unbounded continuation. Missing/truncated/disagreeing ledgers, stopped accounting, or unfinished attempts stop further turns. Legacy completion-only ledgers never supply an upper bound.

The parent supplies remaining request/token/cost allowances to each serial scenario worker, rather than giving each worker the full campaign budget. Worker subprocess timeout is bounded by the remaining explicit deadline. No budget limit is increased. Existing campaign/store isolation, fresh reset and reused-store refusal remain intact. These code paths were tested with stubs and provider-disabled runs; this pass did not invoke a live baseline.

## Deterministic validation and regression

All requested accounting categories have passing deterministic coverage: success, provider exceptions/timeouts, dispatch interruption, admitted/uncompleted attempts, multiple requests, expression-only and interpretation-only usage, no-provider cases, concurrent final allowance, request exhaustion, unknown tokens, duplicate identities/completion observations, early-return telemetry, conditional owners, readiness acceptance/refusal, durable write failures, ledger corruption and remaining-worker-budget propagation. Every production owner was tested for success, provider exception, interruption, and an exhausted allowance; the controlled provider stub is never invoked after refusal. Twelve simultaneous contenders for one allowance yield exactly one dispatch.

| Evidence | Result and scope |
| --- | --- |
| `surface_final.xml` | 59 current lifecycle/dispatch-owner/readiness tests passed, 0 failed/errors/skipped |
| `accounting_final.xml` | Earlier 102 focused accounting/ATGB checks passed before the final completion-write idempotency and application-surface checks |
| `accounting_verified.xml` | 103 checks: 102 passed; one all-scenario reset check hit isolated Windows `os.replace` access denial while saving combat state |
| `preflight_retry.xml` | That provider-disabled reproducibility check passed on targeted retry, exercising two fresh resets for all ten scenarios |
| `regression.xml` | 227 relevant tests: 225 passed, 2 failed; includes provider preflight/routing, expression, semantic planner, conversational orchestration/continuity and ATGB |
| `prior_failures.xml` | Both regression failures reproduced with original budget and original `call_gpt` restored in memory only |

The two pre-existing failures are the exact routing-metadata dictionary expectation (extra `provider_call` field) and missing `answer_sufficiency` in an expression-authority expectation. Neither expectation nor gameplay implementation was altered to clear them. A separate initial owner-test run hit four test-guard wiring failures; the tests were corrected to invoke captured production functions with an explicit fake transport, and the corrected run passed. All attempts and JUnit evidence are retained. The Windows reset-write failure is infrastructure/environment evidence, not a conversational failure. No full-suite claim is made.

## Scope review, provenance, and readiness

`scope_review.json` and `accounting_scope.diff` record the complete campaign code diff against verified pre-repair source bytes. AST comparisons confirm that all seven provider-call argument sets are unchanged. Existing top-level production functions outside the budget owner, seven dispatch functions, and early-return telemetry are unchanged. No semantic routing, interpretation contract, NPC knowledge, narration policy, benchmark fixtures/expectations, model configuration, or gameplay authority was changed.

Original ATGB-03 and ATGB-03A evidence, transcripts, frozen Frontier Gate baseline, corpus, and canonical campaign data are byte-preserved against the initial snapshot. `preservation_checks.json` records allowed infrastructure changes and current source hashes. Repository HEAD is `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`, with the pre-existing dirty worktree retained; no commit was created. Version `ATGB-03B-1` plus hashes identify the actual accounting implementation. Model roles remain gpt-4.1-mini with existing routing settings. Readiness is verified for the reviewed current sources, not for historical trial accounting.

## Known limitations and stop boundary

The request ceiling bounds application admissions in one process, including attempts that never dispatch. It does not count individual SDK transport retries, which remain unchanged. ATGB workers are serial and receive remaining campaign allowances; this is not an account-wide or multi-process distributed quota service. Independently launched utilities with other ledgers need their own budgets.

Durability depends on successful local filesystem writes/flush/fsync. Partial or conflicting evidence fails closed. No automatic crash-resume is implemented: pending attempts stay consumed and existing ledgers cannot restart under zeroed counters. Concurrent mutation between a snapshot and disk read can conservatively cause reconciliation refusal. Unknown usage still stops the bounded run; token admission uses the existing estimates and output reservations, with reported-limit violations stopping subsequent work.

Source fingerprints cover the reviewed application package and entry point; external libraries and future indirect provider mechanisms need renewed inventory/validation. Completed-record-only external consumers must adopt event-aware reconciliation. Durable writes add infrastructure work; no new live latency or cost measurement was made.

No live-provider benchmark, gameplay repair, or Product Realization campaign was run. Original 15/37 captured turns remain pending authorized human scoring; uncaptured outcomes and S07/S09 opening-context delivery remain unmeasured. Readiness acceptance is not permission to continue. Stop after this review handoff and await review before ATGB-03 continuation.
