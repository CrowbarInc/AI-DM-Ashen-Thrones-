# Routing and Dispatch Inventory

Dispatch owners are the `admit_request` call sites in the current working tree. Model strings below are the code defaults unless a ledger recorded a different response model. Live cycles in this audit recorded `gpt-4.1-mini-2025-04-14`. `ENABLE_MODEL_ROUTING` defaults on (`game/config.py` line 67). Primary turns select `DEFAULT_MODEL_NAME`. A retry purpose selects `RETRY_ESCALATION_MODEL_NAME`, which falls back to the same default unless the environment overrides it.

Provider-free responses are a normal outcome. Examination, repeated examination, resolved travel, operational refusal, and a settled adjudication sentence do not require a provider call.

## Routes

| Route | Entry and owner | Eligibility | Prompt owner | Model and output cap | Fallback | Second request | Accounting |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Campaign opening | `call_gpt` when the messages request `scene_opening`. Owner `gm.call_gpt` | New campaign start | `build_messages`, then opening renderer or the opening fact instruction in `gm.py` | Default model. Output cap `ASHEN_OPENING_MAX_OUTPUT_TOKENS`, default 3,000 (`gm.py` 4194, 5348–5349) | Structured rejection and deterministic recovery. No automatic second opening in the F3 script | A failed opening can retry when retries are enabled | Ledger purpose is whatever the caller passes. Historical openings appear as `primary_turn` |
| Primary narration | `api.py` `_bounded_call_gpt` → `gm.call_gpt` | `gm is None` after host-speech adoption and `deterministic_provider_skip_line` | `gm.build_messages` → `prompt_context.build_narration_context`. Profile `manual_play_auto` | Default model. Output cap `ASHEN_NARRATION_MAX_OUTPUT_TOKENS`, default 600 | Visibility replacement, terminal retry fallback, or the budget-refusal sentence | Retry loop calls `call_gpt` again with purpose `retry_escalation` unless `ASHEN_DISABLE_PROVIDER_RETRIES` | Ledger events `admitted`, `dispatch_attempted`, `completed`. Session `performance` has stage milliseconds. No prompt text |
| Bounded expression | `expressive_dialogue.request_expression` | Expression not disabled, and a contract exists. Narration uses `integrated_play.maybe_narrate` when `ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION=1` | Two short messages: system instruction plus committed facts or the speech contract | Default model. Output cap 80 | Host sentence. Validator is local. No second model | One call. No retry (`request_expression` docstring) | Purpose `expression` |
| Live chat interpretation | `live_chat_interpretation.request_interpretation` | Live interpretation enabled and the fast path does not settle the turn | Catalog messages in `live_chat_interpretation.py` | Caller model. Output cap 320 | Operational refusal. `sent` is recorded on the block result | No retry | Purpose `interpretation` |
| Contract interpretation | `semantic_interpreter._invoke_interpretation_model` | Interpreter enabled. Disabled when `ASHEN_DISABLE_LIVE_INTERPRETATION` is set (`semantic_interpreter.py` line 93) | `interpretation_messages` plus a strict JSON schema | Default model. Output cap 400 | Caller handles the refusal exception | Callers do not retry this function | Purpose `contract_interpretation` |
| NPC dialogue wording | Expression path above, after the dialogue owner accepts a line | Named NPC turn with an expression contract. `expression_generation_disabled()` returns the host line | Expression prompt | Cap 80 | Grounded host line. `dialogue_accepted` stays false on grounded fallback | One expression call | Purpose `expression` |
| Clarification | Publication contract `CLARIFICATION_REQUIRED` | Ambiguous reference already classified | None when the contract is in `SKIP_PRIMARY` | No provider call | The clarification sentence is the publication | None from this contract | `narration_skip` |
| Deterministic engine | `deterministic_provider_skip_line` and `narration_skip` | Clue discovery, repeated search, local observation, resolved travel, recalled social topic, determined nonresolution, or a stamped engine publication | None | No provider call | The engine sentence is the publication | A later turn can still call the provider | `provider_narration_skipped` |
| Physical retreat | `physical_adjudication.plan_physical` / `commit_physical`, reached from `bounded_improvisation.controlled_request` | `ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION=1` and controlled world/initiative enrollment | Host sentence, then optional `maybe_narrate` | Expression cap 80 when narration is enabled. Physical interpretation cap 80 and physical plan cap 180 exist behind `ASHEN_PHYSICAL_PROVIDER` | Host sentence when expression is disabled or the candidate is rejected | `narration_skip` stops a second primary call after one expression attempt | Purpose `expression`, `physical_interpretation`, or `physical_plan` |
| Grounded fallback | `force_terminal_retry_fallback` and visibility enforcement in the narration loop | Primary output failed validation, retries exhausted, or retries disabled | No new prompt when retries are disabled | No additional call in that case | Replaces player-facing text and can still publish | The retry itself is the second call when retries are enabled | Tags on the GM object. Ledger row only if a call was sent |
| Admission refusal | `provider_budget.admit_request` | Request, input, output, or total ceiling, or accounting failure | None | No call | Operational sentence. Playtest stop message when SDK retries are disabled | None. `_STOPPED` blocks later admissions | `sent: false` when a rejection row is written. F3’s request-ceiling case wrote the refusal on the session log and did not add a completed gameplay event |

## When a cheap path becomes primary narration

Primary narration runs when all of the following are true:

- Provider calls are not disabled.
- No host speech was adopted.
- `narration_skip` and `deterministic_provider_skip_line` return none.
- The manual-play GPT budget still has a call.

`ASHEN_DISABLE_EXPRESSION_GENERATION` stops `request_expression` and `maybe_narrate`. It does not stop `gm.call_gpt`. A turn that never receives an adjudication or discovery contract therefore still pays for the full narration prompt. That is the F3 step-back.

Disabling live interpretation removes the model interpreter and leaves the deterministic fast path. “I step back from the notice board.” is not matched by `_GENUINE_ACT_RE` or `_PHYSICAL_RE` in `resolution_contract.py` (those patterns cover push, pull, climb, enter, and similar verbs, not “step back”). The fast path stores `unresolved`. With the physical experiment off, nothing else claims the turn.

## Duplicate dispatch

The retry loop can send a second `gm.call_gpt` with the original messages plus a retry instruction. F3 had retries disabled, so the second invocation returned inside `call_gpt` before `admit_request`. One ledger completion. The session counter still says two narration calls.

Historical PR-PLAY-79 did send two `retry_escalation` completions. Those are real second dispatches, each over 28,000 input tokens. They are retries of primary narration, not a second route family.
