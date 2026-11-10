# F3 Incident Reconstruction

Classification of the expensive request: **B, an avoidable routing decision, with A as the policy that made the fall-through legal.** It is not a duplicate live dispatch. The chain is attributable.

## Recorded request

| Item | Evidence | Class |
| --- | --- | --- |
| Utterance | “I step back from the notice board.” `http_acceptance.py` continuation; session log entry 3 | RECORDED |
| Public scene | `frontier_gate`, turn 5 after the examine and the refusal reload | RECORDED |
| Preceding publication | “You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.” | RECORDED |
| Interpretation | `ASHEN_DISABLE_LIVE_INTERPRETATION=1` on the continuation. Contract field `model_interpreter_invoked: false`, `interpretation_api_calls: 0` | RECORDED |
| Expression | `ASHEN_DISABLE_EXPRESSION_GENERATION=1` for the whole script | RECORDED |
| Physical experiment | The HTTP script does not set `ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION` | RECORDED |
| Fast path | `proposal_source: deterministic_fast_path`, `operation: unresolved`, `intent_purpose: request_information`, `operation_eligibility: no_consequential_operation` | RECORDED |
| Narration skip | Resolution has no `kind` and no `publication_contract`. `provider_narration_skipped: false` | RECORDED |
| Dispatch | `admitted` then `dispatch_attempted` then `completed`, owner `gm.call_gpt`, purpose `primary_turn` | RECORDED |
| Model | Configured `gpt-4.1-mini`. Response model `gpt-4.1-mini-2025-04-14` | RECORDED |
| Output allowance | `call_gpt` uses `ASHEN_NARRATION_MAX_OUTPUT_TOKENS`, default 600. Recorded output is 600 | CODE-INFERRED default; RECORDED output |
| Tokens | 22,777 / 600 / 23,377, `usage_consistent: true` | RECORDED |
| Provider latency | 5,339.716 ms on the completed ledger row | RECORDED |
| Server total | `performance.elapsed_ms` 6,166; `narration_ms` 6,032; `interpretation_ms` 35; `resolution_ms` 0; `validation_ms` 13; `retry_ms` 12 | RECORDED |
| Wrapper latency | `provider_call.latency_ms` 5,733 | RECORDED |
| Browser paint | The HTTP script uses `TestClient`. No browser paint sample exists for this call | UNKNOWN |
| Admission | The request was admitted. Ceilings in the script were 4 requests, 100,000 input, 100,000 output, 200,000 total | RECORDED |
| Result | Tags include `visibility_violation:undiscovered_fact_assertion`, `visibility_enforcement_replaced`, `final_emission_gate_replaced`, `forced_retry_fallback`, `provider_retry_disabled` | RECORDED |
| Publication | Pointer advanced. Event `validation_outcome: engine_or_grounded_fallback`. `accepted_expression_references: []`. The visible sentence restates notice-board material and does not say the player stepped back | RECORDED |

## Decision chain

1. The examine turn resolved as `discover_clue` and skipped primary narration (`provider_narration_skip_reason: resolved_clue_discovery`). Zero provider requests. RECORDED.
2. “Good day, Gate Guard.” hit request ceiling 0 and returned the operational refusal. Resolver not run. Zero tokens. RECORDED.
3. Reload kept the examine sentence and turn 5. RECORDED.
4. The continuation re-enabled a request ceiling of 4 and left interpretation and expression disabled. RECORDED in `http_acceptance.py` lines 111–113 and 15–29.
5. The deterministic fast path did not call the interpreter. It stored operation `unresolved` and treated the line as a non-consequential information request. `physical_adjudication._operation` recognizes “step back” as `retreat` (`game/physical_adjudication.py` lines 211–212), and `plan_physical` returns nothing unless `ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION=1` and the controlled-world gate are on (lines 46–48, 819–820). Those flags were unset. CODE-INFERRED from the script environment plus the current source.
6. `narration_skip` returns a host sentence for adjudication, clarification, unsupported action, failure, and repeated examination (`game/publication_contract.py` lines 289–321). None of those contracts were on this resolution. CODE-INFERRED.
7. `deterministic_provider_skip_line` therefore returned none, and `api.py` called `call_gpt` with purpose `primary_turn` (`game/api.py` around 3762–3776 and 3695–3715). CODE-INFERRED.
8. The model output was replaced. Hard validation on the saved fallback text is `hard_valid: true` with empty reasons. The published sentence is that fallback. RECORDED.
9. `ASHEN_DISABLE_PROVIDER_RETRIES=1` made the retry return before a second dispatch (`game/gm.py` lines 5212–5235). The ledger has one `completed` row with `sent: true`. Session counters say `provider_call_count: 2` and `narration_provider_calls: 2` because `_bounded_call_gpt` increments before `call_gpt`. RECORDED counters; CODE-INFERRED reason. This is an accounting overcount, not a second live call.

The saved GM object also carries `model_route_purpose: retry_escalation` beside `provider_call.purpose: primary_turn`. The ledger is the authority for the sent call. The route stamp on the final object describes the unsent retry. RECORDED mismatch; CODE-INFERRED cause.

## Comparison with the inexpensive path

PR-PLAY-79D-F `browser_host.py` enables physical adjudication, player initiative, world improvisation, and expression, and sets admission to 4,000 input / 5,000 total. The retreat resolution there is `kind: interact`, `publication_contract: FINAL_ENGINE_RESPONSE`, `skip_primary_narration: true`, one expression call, 72 tokens. RECORDED.

F3 used the opposite flags and the primary path. The product default leaves the physical experiment off. With that default, plus interpretation off, the fast path’s `unresolved` result is enough to select primary narration. That is current policy once the turn is unresolved (A), and it was avoidable for this utterance because the retreat owner already exists (B).

## What the published sentence was

The continuation is a completed gameplay publication: the pointer moved and the HTTP event was written. It is not an accepted expression, and it does not narrate the retreat. Useful provider-backed publication from the 23,377 tokens: none.
