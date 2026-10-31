# ATGB-03A — Provider accounting safety and continuation readiness

Date: 2026-10-18. Status: BENCHMARK SAFETY CORRECTION VALIDATED; REQUEST UPPER BOUND UNRESOLVED; LIVE CONTINUATION STOPPED; HUMAN SCORING PENDING.

The existing ledger cannot safely establish a request upper bound across the production dispatch surface. The user explicitly required stopping in that case. No additional live requests or trials were executed. The baseline remains partial: S01–S03 complete, S04 two of four turns, S05–S10 unattempted; 15/37 captured turns. This pass does not claim completion of the requested full accounting repair or live baseline.

## Root cause and established evidence

Primary investigative class: evaluation/infrastructure. The harness treats `resolution.metadata.performance.provider_call_count` as an authoritative application request count even though host performance accounting is neither universal nor scoped to every provider purpose. The safety stop itself was correct once the configured count became unavailable.

The earliest captured scope disagreement is S03.2: the independent ledger records an expression request omitted by host accounting. S03's host subtotal is two requests and its ledger records three. The immediate trigger for the stop is S04.2: its HTTP-success reply has `kind=interpretation_rejected`, `processing_outcome=context_leak`, and no performance object. `game/api.py:_live_interpretation_block_response` constructs that early return without performance telemetry; its caller returns before the later ordinary chat finalization that attaches `_performance_record`. The worker marks the absent telemetry unavailable; its next-turn accumulator loses observability and refuses S04.3. No gameplay cause is inferred from that routing evidence and none is repaired.

S04.2's detail counters and public provider-request list are zero/empty. Those values do not prove zero physical or application requests. The original ledger has no turn identifiers or dispatch-start entries, so no new exact turn attribution is asserted. Original raw resolution, worker capture, scenario totals, and source locations are preserved separately in `artifacts/atgb/atgb_03a/original_accounting_analysis.json` and `accounting_readiness.json`.

## Why the existing ledger is insufficient

The existing owner, `game/provider_budget.py`, admits requests in `begin_request`, increments its counter only in `finish_request`, and appends completed/failed records to the durable ledger. All application purposes must pass through that lifecycle for the ledger to enforce an upper bound. Source inspection establishes three coverage gaps:

- `game/semantic_interpreter.py:_invoke_interpretation_model` dispatches without either the budget guard or ledger.
- `game/host_constrained_candidates.py:invoke_candidate_provider` calls the guard, but a dispatch exception can exit before completion accounting.
- `game/unified_semantic_planning.py:_invoke_provider` has the same completion-only exception gap.

The latter two paths have feature gates; this report does not claim they ran in ATGB-03. The unledgered interpretation adapter has its own enabled/consumed conditions. No proof establishes that all possible future benchmark paths exclude these owners, and changing their gates would change evaluation configuration. The audit inventories seven Responses dispatch sites, including startup preflight (skipped by the existing benchmark worker environment). Finding a site is not evidence of a request being sent.

A deterministic reproduction sets an existing request limit of one, admits an attempt, simulates interruption before `finish_request`, observes the unchanged zero counter, and obtains another admission. This uses no provider. Completed ledger rows and the process snapshot can agree while omitting unfinished attempts. A normal request guard test separately verifies that two completed requests exhaust a limit of two. The existing mechanism is useful but insufficient to certify universal coverage. Production accounting was deliberately left unchanged under the user's scope restriction.

## Benchmark-only correction

Accounting version `ATGB-03A-1` adds `tools/atgb/accounting.py`, plus a pre-execution refusal in the runner and direct worker. Live mode stops before creating/resetting a store or importing the game when coverage is not established. The runner writes `accounting_readiness.json` and raises `LiveRunRefused`; the worker returns a structured infrastructure stop. Provider-disabled execution remains available.

`inspect_ledger` reuses the existing durable records and owner snapshot for observed-subtotal reconciliation. It rejects missing files, incomplete records/lines, duplicate request IDs, counter/snapshot disagreement, stopped accounting, and sent rows lacking complete usage/identity. It never sums host counters with ledger counters or fills missing host fields. Empty initialized ledger plus matching snapshot can establish an observed zero subtotal; it still cannot certify an upper bound. Duplicate rows are rejected rather than counted twice or silently collapsed. This helper is diagnostic, not the live budget authority.

The readiness audit is a conservative refusal audit, not a general static coverage proof. It intentionally has no automatic success/bypass path: even a changed inventory requires review. It does not claim that source-name matching proves future provider coverage. A separately reviewed, reliable dispatch lifecycle would be needed to replace the refusal. Token/cost checks and elapsed/request ceilings are retained; no limit is increased. No new conversational fallback, routing, interpretation, dialogue, prompt, model, or scoring rule was added.

## Validation

All 45 focused tests passed with zero failures/errors/skips: 21 accounting checks and 24 existing infrastructure/readiness checks. The retained JUnit file is `artifacts/atgb/atgb_03a/deterministic_host.xml`. Tests cover missing performance, host/ledger disagreement, expression-only usage, no-provider turns, multiple requests, exhausted call/time budgets, incomplete ledger rows, duplicates, snapshot disagreement, interrupted accounting, refusal through both live entry points, reused-store rejection, provider-disabled production chat, and fresh isolated starting-state reproducibility across all scenarios.

The initial sandbox test attempt stalled in the known TestClient environment and was interrupted. The same focused suite passed outside the sandbox, with providers disabled. No live provider was used for debugging or validation. No broad/full-suite result is claimed. Deterministic checks demonstrate safety/refusal and observed reconciliation; they do not demonstrate repaired universal accounting or live completion.

## Trial provenance and continuation decision

The original ATGB-03 trial remains unchanged, including the partial S04 transcript, worker/job, isolated state/log, usage rows, report, and human worksheets. `preservation_before.json` and `preservation_checks.json` verify byte preservation. Production sources, original benchmark corpus, frozen baseline, and canonical campaign data match the initial snapshot. Only the two pre-existing benchmark source files changed; the accounting module, tests, campaign evidence, and report are new. No commit was created. HEAD remains `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`; source hashes supplement the already dirty worktree.

S04.3 cannot safely resume through the supported harness with continuity established. `prepare_isolated_store` rejects a reused marked store; `execute_job` verifies baseline files and then unconditionally hard resets. There is no checkpoint/resume mode or restoration of the process-local accounting owner. Persisted final state is valuable evidence, but it does not validate a supported continuation. No attempt was made to reset or overwrite that state.

After accounting is independently made safe, the plan is to run S04 from its beginning as a separate trial 2, then S05–S10 in separate fresh stores. Keep the trial-1 partial S04 and trial-2 conversation distinct. S01–S03 need no rerun. This is a future plan, not an executed trial. The original configuration remains gpt-4.1-mini for every configured role, routing enabled, frozen `frontier-gate-v1` manifest `4197114379ba9c406d9b2135085eb605d8235fd9a34dcebe852b95451ef41ae9`.

The original limits were 80 application requests and 1800 elapsed seconds, with 300 seconds per scenario. The original wall-clock deadline has expired. A future continuation needs an explicit fresh deadline and a conservatively established remaining request allowance. Twelve requests are observed; subtracting that subtotal to declare 68 guaranteed remaining would overstate accounting completeness. `continuation_plan.json` records this limitation rather than inventing a safe remaining budget.

## Usage, opening context, scoring, and handoff

ATGB-03A adds zero live requests. Original observed usage remains 12 sent application requests: 11 interpretation and one expression; 21,531 input and 2,190 output tokens in recorded rows. Host count is a known subtotal of 11 plus one unavailable turn. Original host latency exists for 14/15 turns (89–4155 ms); S04.2 remains unavailable. Recorded scenario wall time is 35.632 seconds. Original provider IDs, usage, model IDs, and latencies remain in the raw ledgers and copied telemetry summaries. SDK-internal transport retries are not separately measured. Dollar cost is unavailable.

S07/S09 opening-context delivery remains unmeasured (`delivered=null`), because neither scenario executed. The future plan requires capturing actual player-visible opening output and its source before the first turn; authored seeds alone are insufficient. No narrative is inserted or expectations altered.

Original worksheets for all 15 captured turns are copied byte-for-byte into this pass and included with the original transcripts. All interpretation, response, authority, severity, clarification, continuity, and conversation-quality judgments remain pending authorized human review. The other 22 turns have no response and no conversational failure score. There are no evaluated successes/failures or invented gameplay scores. Infrastructure failures and unmeasured outcomes remain distinct.

The standard handoff is `handoff/CURRENT_REVIEW.md`, `REVIEW_MANIFEST.json`, and `CURRENT_REVIEW.zip`, with history under `atgb_03a_provider_accounting`. Review the accounting limitation and pending original conversations. No gameplay repair or Product Realization campaign is initiated. Stop here pending review.
