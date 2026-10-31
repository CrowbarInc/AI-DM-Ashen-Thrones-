# PR-ED review — Provider Efficiency and Responsiveness

Decision: **B — PR-ED ACCEPTED WITH LIMITATIONS**

## 01 — Executive summary

PR-ED measured the production player turn before changing it, then removed work that the measurements showed was paid for and then discarded.

What was investigated: the live path from `/api/chat` through interpretation, orchestration, authoritative resolution, narration, validation, retries, and persistence. Provider calls, token counts, and retry reasons were recorded on a disposable courtyard. A bounded live sample used `gpt-4.1-mini`.

What changed:

- A completed scene transition or travel result, and a local observation the engine already overwrites, no longer call the narration provider.
- A narration retry that was never sent, or that would resend identical text after at least one attempt, stops instead of calling the provider again. It does not resolve the action again.
- A duplicate copy of `response_policy` and matching contracts inside `turn_packet` is omitted from the narration payload.
- Narration and interpretation clients use `ASHEN_PROVIDER_TIMEOUT_SECONDS`, default 45, clamped from 5 to 120.
- Each narration call records purpose, whether it was sent, latency, and token counts. The turn trace records a compact performance object. Neither stores prompts, keys, or the world.

Principal finding: on this machine the engine spends tens of milliseconds. The player waits on the provider. One completed move spent 16.6 seconds and about 47 thousand input tokens on two generations that validation discarded. The player still received the deterministic arrival sentence the engine already had.

Demonstrated improvement: that move now returns in 101 ms with zero provider calls and the same arrival sentence. The scene still changes once.

Remaining limitations: ordinary NPC dialogue still takes about 3 seconds and about 23 thousand input tokens. Eight of the ten representative turns were not remeasured live after the change. Inherited social and exploration failures remain. Richer model prose is no longer requested for a completed transition.

## 02 — Preimplementation baseline

Repository, configuration, regression counts, and the pre-edit measurements are in `PR-ED_preimplementation_baseline.md`.

Short form:

- Revision `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` on `feature/product-realization`, working tree already dirty.
- Regression before edits: 249 passed, 30 failed, 20.09s. JUnit: `artifacts/pr_ed_provider_efficiency/baseline_junit.xml`.
- Disabled-provider 10-turn profile: 12 narration calls, median engine time 74.5 ms.
- Clean live movement before edits: 16646 ms, 2 calls, 22138/917 then 25207/1117 tokens.
- Clean live dialogue before edits: 3111 ms, 1 call, 23469/61 tokens.

Instrumentation before the production edits was external wrappers only. Production timing fields were added with the optimizations. They do not add provider calls or serialize the world.

## 03 — Production turn trace

Actual path for a normal player message:

1. Browser `POST /api/chat`.
2. `game.api.chat` marks the turn clock.
3. Communication-mode and explicit out-of-character handling can return with no provider call.
4. `deterministic_conversational_decision` handles answer, clarify, plan, and decline with no narration call. Execute continues.
5. Live interpretation runs only when that decision abstains and live interpretation is enabled. One call, no retry. Pytest disables it.
6. Existing parsers and resolvers commit the authoritative result.
7. `_build_gpt_narration_from_authoritative_state` builds the prompt and calls `call_gpt`, then may retry.
8. Final emission, arrival and perception realization, and persistence run after narration.
9. The response includes `trace.performance` and `resolution.metadata.performance`.

Fields recorded where the engine has them: turn and scenario identifiers in the profiler, category, elapsed milliseconds, provider-call count, input and output tokens, retry count and reason, persistence time, disposition, and whether the player-facing response succeeded. Stage times are the provider latencies already attached to the call. Interpretation, resolution, narration, and validation are not separate clocks beyond those call records. Persistence is the wrapped `save_session` and `save_world` time.

The trace does not store prompts, responses, credentials, or the world snapshot.

## 04 — Provider call inventory

| Call | Component | When | Mandatory | Classification |
| --- | --- | --- | --- | --- |
| Live interpretation | `interpret_production_turn` | Deterministic orchestration abstains and live interpretation is on | Conditional | C. One call. Not retried. Not measured live on the clean movement and dialogue samples, because those turns were decided before interpretation. |
| Narration, structured realization | `_build_gpt_narration_from_authoritative_state` | Consequential or declared turns that still need model prose | Required for dialogue and unresolved narration | D for social dialogue. A for a completed scene transition whose player text is already the arrival sentence, and for a local observation the engine overwrites after the call. |
| Narration-only envelope | `select_provider_response_envelope` | Incidental dialogue with no declaration and no consequential result | Conditional | D. Left unchanged. Prior tests lock this envelope. It was not broadened. |
| Targeted narration retry | `gm_retry`, up to 2 attempts, social capped at 1 | Timeout, rate limit, connection, server error, malformed output, scene stall, unresolved question, hard-invalid narration | Conditional | B for an unsent call or a retry whose text is identical to the previous attempt. D for a first retry that changes the text or the failure conditions. |
| Social repair and fallback | existing emission repair | After the provider returns or after retries stop | Conditional | D. Not bypassed. |

Redundancy that the measurements support:

- Ordinary movement generated narration and then discarded it. Safe to skip after the resolver has a target scene. Evidence: live baseline player text equals the arrival template, and both generations failed validation.
- Local observation calls the provider and then replaces the text with `realize_local_observation_line`. Safe to skip. Evidence: the overwrite is unconditional on that lane.
- `turn_packet.response_policy` repeated the root policy. Safe to omit when the JSON is equal. Dialogue input fell by 434 live tokens. The payload object passed in is not mutated.
- Scene-stall and hard-invalid retries resend the full prompt. Stopping when the provider was not sent, or when the text did not change, removes a repeated call. The first changed retry remains.

Not treated as redundant: authoritative resolution, final-emission checks, social dialogue generation, and a retry whose output actually changed.

## 05 — Token consumption audit

Estimate method in the profiler is character length divided by 4. On the live movement prompt that estimate was 22740 and the provider reported 22138. Close enough to rank components. Live counts are the figures used for claims.

Largest pieces of the movement narration prompt, estimated tokens:

- Root `response_policy`: about 5179
- `instructions`: about 3687
- `turn_packet`: about 2700, of which the nested policy was about 1524 and contracts about 957
- System structured-realization prompt: about 2391, driven by the declared-claims schema
- `narrative_plan`: about 1611

The duplicate nested policy is the piece that was removed. It is small next to the system schema and the instruction block. Those were not cut. Cutting them would risk the context the model needs for NPC identity, player knowledge, and authorized outcomes, and this cycle did not run a context-starvation suite against a smaller schema.

What was checked after the small cut, on the disabled-provider profile and focused tests:

- "Where are we?" still returns the courtyard summary, including after a move in the continuity test.
- Compound intent still clarifies and does not execute either step.
- Completed movement still names the waystation street and does not invent a watchtower.
- Dialogue still reaches Sergeant Mara. The live sentence is unchanged.

Conversation history, opening-scene instructions, and the structured schema remain the large residual cost. Opening instructions attach when `turn_counter <= 1`. Fast conversational turns return before that counter advances, so the first consequential turn is often treated as an opening.

## 06 — Retry and validation audit

Who retries: the narration loop in `_build_gpt_narration_from_authoritative_state`. Interpretation does not retry. Resolution runs before this loop.

What triggers a retry: upstream timeout, rate limit, server error, and connection error; content failures including scene stall, unresolved question, and hard-invalid narration through `run_preserve_if_valid`. The retry message is added to the same prompt. Maximum targeted attempts remain 2. Social remains capped at one content retry. `MANUAL_PLAY_MAX_CALL_GPT` remains 6.

Classification:

- Transient provider failure: timeout, rate limit, network, server error. Still retried when a call was sent, within the existing ceilings. The new 45-second timeout bounds a hung call. Observed successful calls were about 3 to 9 seconds, so this default did not cut them off.
- Recoverable generation failure: malformed or invalid narration. A first retry that changes the text is still allowed.
- Deterministic contract failure: an unsent call, or a second attempt whose text equals the previous text. `narration_retry_should_stop` ends the loop, uses the existing terminal fallback, and does not call the provider again.
- Authority failure: still rejected by the existing emission checks. Those checks were not weakened.

Invariant: a narration retry does not repeat a committed consequential operation. The skip and the retry stop sit inside narration, after resolution. They replace narration text only. The movement test asserts the destination scene is active and `call_gpt` was not invoked. The retry stop calls `force_terminal_retry_fallback` and does not re-enter the resolver.

The live movement baseline is the evidence that a retry can dominate latency: the second call cost 25207 input tokens and about 9.3 seconds and was discarded. That turn no longer reaches the retry because the provider call is skipped.

## 07 — Optimization inventory

| Change | Original behavior | Affected turns | Expected benefit | Authority risk | Evidence |
| --- | --- | --- | --- | --- | --- |
| Skip narration when the resolver already has a scene-transition or travel arrival line | One or more provider calls, then the arrival sentence | Completed movement | Removes the dominant measured wait | Scene must already be committed. Social turns are excluded. | Live 16646 ms to 101 ms, same sentence, scene changes |
| Skip narration for local-observation questions | Provider call, then unconditional overwrite | Local observation | Removes a discarded call | The line is the existing observation function | Helper test returns that line. Not a live sample |
| Stop identical or unsent narration retries | Full prompt resent | Stalled or invalid narration | Avoids a repeat that cannot change | Does not re-resolve. A changed retry still runs | Disabled profile: alternative wording 3 calls to 1. Live identical-retry case was not remeasured because movement no longer calls |
| Omit duplicate turn-packet policy | Same policy sent twice | Narration prompts whose nested policy matches | About 400 input tokens on the live dialogue sample | None when JSON differs; the nested copy is kept | Dialogue 23469 to 23035 input, same sentence |
| 45-second provider timeout | SDK default, about 600 seconds | Every narration and interpretation call | Bounds a hung call | A slow valid call beyond 45 seconds will time out and may retry under existing rules | Successful samples were under 10 seconds |

Not done, because the evidence did not justify them: switching consequential turns to the narration-only envelope, keyword intent handlers, a second classifier, a smaller declared-claims schema, or fewer social retries.

## 08 — Performance comparison

Comparable live samples use the same model, the same courtyard seed, and `--max-output 1600 --input-limit 120000`. Sample size is one turn per row. Provider variance is real. A few hundred milliseconds on a single dialogue call is not treated as an improvement.

| Observation | Baseline | Optimized | Change |
| --- | --- | --- | --- |
| Ordinary movement latency | 16646 ms | 101 ms | −16545 ms |
| Ordinary movement provider calls | 2 | 0 | −2 |
| Ordinary movement input / output tokens | 47345 / 2034 | 0 / 0 | −47345 / −2034 |
| Ordinary movement retries | 1 hard-invalid | 0 | −1 |
| NPC dialogue latency | 3111 ms | 2777 ms | −334 ms, one sample |
| NPC dialogue provider calls | 1 | 1 | 0 |
| NPC dialogue input / output tokens | 23469 / 61 | 23035 / 73 | −434 / +12 |
| NPC dialogue retries | 0 | 0 | 0 |
| Disabled-provider narration calls, 10 turns | 12 | 7 | −5 |
| Disabled-provider median engine time, n=10 | 74.5 ms | 76.5 ms | engine time, not player wait |

Median and P90 across mixed live turn types are not reported. The only clean live pair is two categories, one turn each. The first 10-turn live run is excluded because a 600-token output cap truncated movement and the input ceiling refused later turns.

Disabled-provider sorted elapsed milliseconds after the change: 3, 20, 72, 74, 75, 78, 81, 82, 83, 109. Those times exclude provider wait.

Classification: movement is a demonstrated improvement. Dialogue token reduction is measured and small. Dialogue latency is not a demonstrated improvement. The 10-turn call reduction is a probable player-facing improvement for completed moves and for identical retries, measured live only for the move.

## 09 — Player-facing quality comparison

Same authoritative courtyard. Wording equivalence was not required.

| Turn | Baseline player text | Optimized player text | Judgment |
| --- | --- | --- | --- |
| Where are we? | Courtyard summary with lantern and gate | Same summary | Continuity and grounding held |
| I go through the courtyard gate. | Arrival sentence naming the waystation street and notice board | The same sentence. Live and disabled. Scene is the street | Intent and authority held. Richer model prose is no longer requested |
| I make for the waystation courtyard. | Disabled provider, three calls, a longer street line plus a taxes-and-curfew sentence | Disabled provider, one call, the shorter street line without the taxes sentence | Fallback text changed because an unsent retry now stops. Not a live quality sample |
| Ask Sergeant Mara about the road | Live: she names the north road. Clue discovered | Live: the same sentence. Clue discovered | Intent, NPC identity, and authority held |
| Which road did you mean? | Disabled: provider-disabled notice | Same notice | Live follow-up was not remeasured |
| I look at it more closely. | Disabled: "notice board" | Same | Grounding held in this fixture |
| The lantern. | Disabled: a fragments line about the street | Disabled: "The guard says, I do not know enough to answer that." | Fallback wording changed. Live clarification was not remeasured. This is the main quality caveat |
| I examine the courtyard lantern. | Disabled: street description | Same description | No live sample |
| Examine the lantern and then go through the gate | Clarification that names both steps and does not do them | The same clarification | Compound handling held |
| Leave the conversation and look around | Disabled: provider-disabled notice | Same notice | Exit path still resolves as observe |

Intent fidelity, authority, and grounding held on the turns that were compared live. The clarification fallback under a disabled provider is a wording change, not evidence that live clarification got worse, and not evidence that it stayed equally useful. That gap is a limitation, not a hidden pass.

## 10 — Live-provider evaluation

Attempted. Credentials were present and were not printed or modified.

Configuration: `gpt-4.1-mini`, routed model `gpt-4.1-mini-2025-04-14`, output cap 1600, input ceiling 120000, timeout 45 seconds on the optimized runs. Accounting was enabled only inside the profiler so usage could be recorded.

Executed live before edits: ordinary movement and NPC dialogue initiation, plus a contaminated 10-turn run that is not a baseline.

Executed live after edits: ordinary movement and NPC dialogue initiation only.

Not remeasured live after the change: simple contextual question, alternative movement wording, NPC follow-up, ambiguous inspection, clarification continuation, straightforward examination, compound intention, and conversation exit. The disabled-provider profile covers all ten for call counts and fallback text. A further live batch was not run. The cycle budget stayed on the two turns that dominated measured cost.

Failures: the movement baseline's narration failed validation twice. The optimized movement made no provider call. Dialogue succeeded both times.

Unavailable: a live median or P90 over the ten-scenario set; live interpretation latency; live token counts for the eight turns that were not remeasured.

## 11 — Regression comparison

Baseline command family, then the same command plus `tests/test_pr_ed_provider_efficiency.py`.

| Run | Passed | Failed | Time |
| --- | --- | --- | --- |
| Before edits, 279 tests | 249 | 30 | 20.09s |
| Final, 286 tests | 256 | 30 | 20.87s |

The seven additional passes are the new PR-ED tests. The 30 failure names are the same set as the baseline. No baseline failure was resolved. No new failure remains in the final JUnit (`artifacts/pr_ed_provider_efficiency/after_junit.xml`).

Inherited failures, unchanged signatures in the final run:

- `test_chat_fallback_preserves_endpoint_specific_no_resolution_shape`
- Dialogue-lock fillers `scene_hold_filler` and `visible_intro_filler`
- Direct NPC question unknown fallback, known follow-up, targeted retry count and priority, unresolved known-fact fallback, speaker-grounded uncertainty (`1 == 2`), repeated social questions
- Social pressure, active-target command routing, mixed-turn adjudication metadata
- Four mixed scene-object investigation cases
- Action-outcome contract inside a social scene, parenthetical rules lane, sanitizer scaffold labels
- Social blob repair, advisory prose, repeated interruption, clean refusal after emit repair
- Wrong opening speaker repair, ragged stranger fallback
- Quarterstaff attack mechanical resolution, two observe-area resolution kwargs, `resolved_exploration_action` absent

Intermediate runs, disclosed:

- Before the exploration assertion was updated, `test_scene_transition_with_known_target_activates_before_narration` failed because `call_gpt` was no longer called. Scene activation had already succeeded. The test now accepts the deterministic arrival sentence, requires the destination scene, and requires that the mock phrase "street narrows" is absent. It passed in the final suite.
- `test_runtime_scene_overlay_persists_and_active_scene_merges_without_scene_file_write` failed once with Windows `PermissionError` WinError 5 during atomic `session.json` replace, passed in isolation, and passed in the final suite. That is the inherited file-lock flake, not a new persistence regression.

Critical authority and duplicate-execution checks in the new tests passed: the move changes the scene once, dialogue still calls the provider and stays in the courtyard, and a narration retry stop does not re-resolve.

## 12 — Remaining bottlenecks

1. NPC dialogue prompts. About 23 thousand input tokens and about 3 seconds for one short reply. Highest remaining player-facing cost. A useful cut has to keep NPC identity, player knowledge, and the authorized clue. This cycle did not attempt that cut.
2. Structured realization schema and instruction block. Together they are larger than the duplicate policy that was removed. They still apply to consequential narration that is not a completed move.
3. Opening-scene instructions on the first consequential turn, because earlier conversational turns do not advance `turn_counter`.
4. Content retries that change the text still resend the full prompt. That remains correct, and it remains expensive when validation fails.
5. Live interpretation is an extra call on turns deterministic orchestration does not decide. Its live cost was not measured here.
6. Persistence is about 10 to 20 milliseconds. It is not the wait the player feels.

## 13 — Final recommendation

**B — PR-ED ACCEPTED WITH LIMITATIONS**

The completed-move path is a demonstrated responsiveness improvement: 16.6 seconds and two discarded generations became 101 milliseconds and the same arrival sentence, with the scene change still owned by the resolver. Dialogue quality on the one live sample was unchanged, and its token drop is real and small. The regression suite added no lasting failure. The inherited social and exploration failures are still there.

This is not an unqualified accept. Most of a session is not a completed move. Dialogue remains a multi-second turn. Eight scenarios were not remeasured live. The clarification fallback text changed when the provider was disabled. Richer movement narration is no longer requested even if a future model would have passed validation.

No further cycle should start from this review until it is accepted.

## 14 — Changed-file inventory

| File | Purpose |
| --- | --- |
| `game/api.py` | Turn clock, performance record, narration skip, identical-retry stop |
| `game/gm.py` | Provider timeout, duplicate policy omission, call timing and token stamp |
| `game/live_chat_interpretation.py` | Same timeout on the interpretation client |
| `game/api.py` narration helpers | `narration_retry_should_stop`, `deterministic_provider_skip_line` |
| `tests/test_pr_ed_provider_efficiency.py` | Skip, retry-stop, duplicate-policy, continuity |
| `tests/test_exploration_resolution.py` | Scene-transition test accepts deterministic arrival |
| `tools/measure_pr_ed_turn_profile.py` | Disposable-world profiler. No secrets printed |
| `artifacts/pr_ed_provider_efficiency/` | JUnit, profiles, live usage, this review |
| `PR-ED_preimplementation_baseline.md` | Pre-edit revision, tests, and measurements |
| `handoff/CURRENT_REVIEW.md` | Short review entry |
| `handoff/REVIEW_MANIFEST.json` | Package index |

Source references: `provider_timeout_seconds` and `omit_duplicate_turn_packet_policy` in `game/gm.py`; `narration_retry_should_stop` and `deterministic_provider_skip_line` in `game/api.py`.

Validation commands:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_exploration_resolution.py::test_scene_transition_with_known_target_activates_before_narration tests\test_pr_ed_provider_efficiency.py --tb=short -q --override-ini="addopts="
.\.venv\Scripts\python.exe -m pytest tests\test_pr_ea_conversational_orchestration.py tests\test_pr_eb_conversational_continuity.py tests\test_turn_pipeline_shared.py tests\test_pr_du_player_pipeline.py tests\test_pr_dq_ic_ooc_messages.py tests\test_social.py tests\test_pr_br_qualifier_movement_mixed_intent.py tests\test_exploration_resolution.py tests\test_exploration_skill_checks.py tests\test_unparsed_movement_state_narration_integrity.py tests\test_save_load.py tests\test_runtime_persistence_regression_suite_obj14.py tests\test_final_emission_gate.py tests\test_final_emission_response_type.py tests\test_pr_ec_movement_partial_intent.py tests\test_pr_ed_provider_efficiency.py --tb=no -q --basetemp=codex_pytest_tmp_pr_ed_after2 --junitxml=artifacts/pr_ed_provider_efficiency/after_junit.xml --override-ini="addopts="
.\.venv\Scripts\python.exe tools\measure_pr_ed_turn_profile.py --out artifacts\pr_ed_provider_efficiency\after_profile.json
.\.venv\Scripts\python.exe tools\measure_pr_ed_turn_profile.py --live --only ordinary_movement --max-output 1600 --input-limit 120000 --out artifacts\pr_ed_provider_efficiency\after_live_movement.json
.\.venv\Scripts\python.exe tools\measure_pr_ed_turn_profile.py --live --only npc_dialogue_initiation --max-output 1600 --input-limit 120000 --out artifacts\pr_ed_provider_efficiency\after_live_dialogue.json
```

Focused tests after the exploration assertion update: 8 passed. Final comparison suite: 256 passed, 30 failed.
