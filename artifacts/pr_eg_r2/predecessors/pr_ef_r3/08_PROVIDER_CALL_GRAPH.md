# 08 — Provider Call Graph

Ordinary gameplay uses one interpretation call and, only when a resolver still needs wording, one narration call plus at most one retry. There is no second interpreter, no ownership model, and no separate validation model. Validation is local and can trigger the retry.

| Call | Trigger | Function | Model | Prompt source | Context | Budget | Retry | Timeout | Output used? | Mandatory? |
|---|---|---|---|---|---|---|---|---|---|---|
| `interpretation` | No stored interpretation and the deterministic fast path did not return | `interpret_production_turn` → `request_interpretation` | `gpt-4.1-mini` | `production_interpretation_schema` plus the appended ownership instructions in `interpret_production_turn` | Scene summary, visible catalog, two visible turns, public evidence, compact ownership context | Output cap 320. No retry. | None | Default 45s; R2 harness 25s | Yes, unless the call fails | Conditional. Skipped for stored interpretations, OOC, and fast-path returns. Movement turn 11 used zero calls. |
| `strict_social` | Social route and no authored line already satisfied the turn | `game/api.py` `_bounded_call_gpt` → `game/gm.py` message builder | Same model | `SYSTEM_PROMPT` plus a JSON user payload | Scene, policy, contract, narrative plan, visibility, obligations | Output cap 1600 in the R2 harness | Failure schedules `retry_escalation` | Same timeout | Only if validation accepts it | Conditional |
| `primary_turn` | Narration that is not on the strict-social route | Same builder | Same | Same, or `NARRATION_ONLY_SYSTEM_PROMPT` when the contract says narration-only | Same family of payload | Same | Same one retry | Same | Same | Conditional |
| `retry_escalation` | `retry_attempt >= 1` or a retry reason | Same builder, purpose forced | Same. Metadata may say escalated; the configured model does not change | Prior payload plus retry instructions from `immutable_valid_response` | Full prompt resent | Same cap | Stops after one | Same | Only if the retry validates. In the expensive turns it did not | Conditional |
| Fast fallback | Provider error or the manual budget of 6 narration calls | `force_terminal_retry_fallback` | None | None | Local | None | None | None | Yes, as an error response | Conditional |

Not present as provider calls: conversational ownership, a second interpretation, context reconstruction, and a separate validator. Ownership is a field on the interpretation call. Context reconstruction is local. Validation is local and is what causes the retry.

## What is necessary

- Interpretation is necessary for sentences the deterministic path does not already understand. Measured size is about 1,600–2,000 input tokens.
- Narration is necessary when the resolver has an outcome and no authored sentence. It is not necessary when the social resolver already selected a public topic. Turn 7 demonstrated that skip. It is also not necessary when speech authority is already `none` and the only legal sentence is the safe line. Turns 3, 5, and 10 still called the model twice and then used the safe line.
- The retry is a real validation repair, not a duplicate interpretation. It is redundant when the first failure is "no authorized fact," because the retry is told to keep the same contract and still has nothing new to say. Those three retries were discarded work.
- GM evidence answers and the safe line are local. They should not be counted as provider work. Cases B, C, and D were one interpretation call each.

The builder already drops some duplicated policy objects (`omit_exact_duplicate_provider_contracts`, `omit_duplicate_turn_packet_policy`). The persisted turn-33 renderer inputs still repeat Mara's id across interaction context, continuity, the narrative plan, the turn packet, and referent tracking. That is structural repetition. It is not a measured token split, because the historical payloads were not stored.
