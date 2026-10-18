# PR-DF Cost and Latency Model

No new measurements were taken. No prices are stated. Token figures that are arithmetic on PR-DE byte counts are labeled `ceil(bytes/4)`. PR-DE already warns that this is not provider usage and not API cost. `tiktoken` was unavailable in that cycle and was not installed in this one.

Output-token counts were not measured for any fixture. They stay symbolic.

## Candidate A — measured input size, unmeasured output

PR-DE revised `build_messages` sizes (system prompt plus user JSON, `ensure_ascii=False`):

| Fixture | Revised bytes | `ceil(bytes/4)` input estimate | Envelope |
|---|---:|---:|---|
| S1 preference | 87,583 | 21,896 | narration_only |
| S2 follow-up | 87,152 | 21,788 | narration_only |
| C1 consequential | 97,373 | 24,344 | narration_only |
| H1 hidden | 96,449 | 24,113 | narration_only |
| F1 factual | 99,163 | 24,791 | narration_only |
| K1 skill (synthetic) | 81,959 | 20,490 | structured |
| B1 combat (synthetic) | 110,769 | 27,693 | structured |
| M1 movement | 94,305 | 23,577 | structured |
| O1 observation | 93,591 | 23,398 | structured |

The 21,896 figure is `ceil(87583/4)`. The same function produces the other rows. PR-DE's "tokens saved" column is the reduction from the pre-dedup payload, not the remaining total.

Provider calls on a completed A turn:

```
calls_A = I + N + R
```

- `I` is 0 when interpretation is pinned off (the experiment pin). On production `chat`, `I` is 1 only if the fast path abstains, a model proposal is appropriate, and live interpretation is enabled. That call is capped at 400 output tokens in `semantic_interpreter.py` and is not retried there.
- `N` is 1 when the turn reaches `_build_gpt_narration_from_authoritative_state`. `N` is 0 for a pending check, an off-scene target, an engine adjudication prompt, or a diplomacy resolution that returns without a provider call (PR-CK records one such persuasion line).
- `R` is the number of targeted narration retries, `0 <= R <= 2` (`MAX_TARGETED_RETRY_ATTEMPTS`).

Completed-turn input estimate:

```
input_A = I * input_interpretation + (N + R) * input_narration
```

`input_narration` is the table above for that fixture. `input_interpretation` was not measured. It is a small candidate list plus two visible turns (`player_visible_turns` limit 2). It is not assumed to be negligible in a live total, and it is not assigned a byte count here.

`R` retries resend a narration payload. A cheaper first prompt does not shrink a turn that retries. PR-DE did not measure first-attempt acceptance, so `R` is unknown for these fixtures.

S1 context mix that still drives `input_narration`: `response_policy` 22,698 bytes, `instructions` 13,947, `gm_resolution_decision` 8,349, `decision_facing_answer_recipe` 6,707, `referent_tracking` 4,501, narration-only system prompt 4,170.

## Candidate B — formula only

```
calls_B = P + Q + N + R
input_B = P * input_plan + Q * input_plan_2 + (N + R) * input_narration
```

- `P` is 1 planner call on turns that use the planner. Experiment cap: one replan, so `Q` is 0 or 1.
- `input_plan` includes the utterance, the referent catalog projection, discourse focus, and the plan schema. **Not measured.**
- `N` and `R` and `input_narration` are the same as A when the narration stage is reached. The first experiment does not shrink that payload. B's planner tokens are added to A's narration tokens.
- Local resolver work is not a provider call.
- A turn that stops at clarification has `N = 0` if the engine line is used, matching A's pending-check short circuit.

A smaller plan request can still make `input_B` larger than `input_A` once `Q`, `N`, and `R` are included. The comparison metric is `input_B` for a **successful** turn, not `input_plan` alone.

## Candidate C — formula only

```
calls_C = sum over rounds r of 1, for r = 1..R_rounds, plus N + R
input_C = sum over rounds of input_round(r) + (N + R) * input_narration
```

- `R_rounds` is at most 4 in the experiment. Each round's prompt contains the tool schema, the conversation so far, and prior tool results.
- `input_round(r)` grows with `r`. **Not measured.** No claim is made that a short tool schema yields a shorter completed turn.
- Read tools add result bytes to later rounds. They do not add world state.
- `request_action_execution` and the single time tool are local. They add latency on the engine side and add result bytes to the next round.
- The narration term is again the full A payload on the first experiment.

Upper bound the harness must record, not assume:

```
input_C <= 4 * input_round_max + 3 * input_narration
```

`input_round_max` is observed during the run. It is not filled in here. The `3 * input_narration` term allows the original narration call plus two retries.

## Latency contributors

Existing keys, with no millisecond baseline in PR-DE:

| Key | When |
|---|---|
| `intent_classification` | chat classification |
| `engine_resolution` | mutation stage |
| `prompt_construction` | payload build |
| `gpt_call` | provider narration |
| `retry_loop_total` | narration retries |
| `fallback_repair` | deterministic repair |
| `final_emission_gate` | emission finalizer |

For B, add `planner_call` and `replan_call` as harness timers. For C, add `tool_round` per round and `tool_handler` per tool. Handler time for current resolvers should be compared with A's `engine_resolution`, not with `gpt_call`.

Expected dominant term on S1-class turns, from the byte table rather than from a clock: the narration provider call. Planner and tool rounds are extra provider waits. They are not assumed faster.

## Context growth across a session

A grows by the session fields the payload already includes (recent log, conversational memory, ledger, clocks, known clues). PR-DE S1→S3 revised bytes are 87,583, 87,152, and 87,097. That is not a growth series: the fixtures differ in utterance and turn index, and S3 is slightly smaller than S1 in that table. Do not read it as "history is free."

B adds plan JSON to the harness log. That JSON enters the narration payload only if a later change puts it there. The first experiment leaves it out of `build_messages`.

C adds tool transcripts to later rounds of the same turn. Across turns, those transcripts are not world state. Persisting them into the next turn's narration payload is forbidden in the first experiment, or the growth term must be counted in `input_narration`.

## Retry exposure

| Architecture | Bound |
|---|---|
| A narration | 2 targeted retries, existing |
| A interpretation | 0 retries, existing |
| B planner | 1 replan, experiment rule |
| C tools | 4 rounds, experiment rule |
| B and C narration | same 2 retries as A |

A validator failure after a successful resolver still costs `R` narration payloads. B and C do not get a larger narration budget.

## What this model refuses to conclude

It does not say B or C is cheaper. It does not say A is cheaper once unusual turns need retries. It says A's narration input for the published fixtures is the measured addend, and B and C must publish the sum of their own calls before any cost claim.
