# 09 — Token Cost Attribution

Source: `artifacts/pr_ef_r2/conversation_3.usage.jsonl`, joined to `conversation_3.json` by each turn's `provider_calls` count. The join consumes all 17 usage rows. Figures below are measured provider usage, not estimates.

| Purpose | Calls | Input tokens | Output tokens |
|---|---:|---:|---:|
| interpretation | 10 | 19,277 | 1,781 |
| strict_social | 4 | 96,180 | 376 |
| retry_escalation | 3 | 81,655 | 233 |
| Total | 17 | 197,112 | 2,390 |

Total tokens 199,502. Output is 1.2 percent of the total. Turn 11, "I walk through the courtyard gate," used no provider call.

| Turn | Player | Calls | Input | Output | What the calls were |
|---:|---|---:|---:|---:|---|
| 1 | Describe surroundings | 1 | 1,704 | 193 | interpretation |
| 2 | What do I know about the lantern | 1 | 1,873 | 191 | interpretation |
| 3 | I ask Mara what troubles her | 3 | 50,565 | 290 | interpretation 2,013; strict_social 22,783; retry 25,769 |
| 4 | Which road do you mean | 2 | 25,876 | 255 | interpretation 2,011; strict_social 23,865, accepted |
| 5 | Who forged the lantern | 3 | 54,315 | 357 | interpretation 2,010; strict_social 24,442; retry 27,863 |
| 6 | GM, clarify what Mara said | 1 | 1,944 | 183 | interpretation |
| 7 | I turn to Mara and ask about the north road | 1 | 1,920 | 216 | interpretation only; authored topic |
| 8 | I inspect the lantern | 1 | 1,928 | 176 | interpretation only |
| 9 | Drop the outstanding request | 1 | 1,930 | 147 | interpretation |
| 10 | Tell the sergeant to describe the courtyard | 3 | 55,057 | 382 | interpretation 1,944; strict_social 25,090; retry 28,023 |
| 11 | Walk through the gate | 0 | 0 | 0 | deterministic move |

The three expensive turns are 3, 5, and 10. Each is an NPC question with no authored answer. Each shows the stock inability line. Their narration and retry outputs were not the player-facing text.

## Required questions

1. Relevant context. Interpretation of those turns fit in about 2,000 input tokens and was enough to name Mara and the operation. That is the measured relevant interpretation cost. The narration payload's relevant share is not measurable from stored records.
2. Unrelated context. Not measurable as a token count. The narration call is about eleven times the interpretation call (22,783 versus 2,013 on turn 3) for a reply of 71 output tokens that was discarded.
3. Repeated sections. Historical prompts were not persisted, so repeated sections cannot be listed as measured text. Current `SYSTEM_PROMPT` is 9,564 characters (about 1,097 whitespace-delimited words). `NARRATION_ONLY_SYSTEM_PROMPT` is 4,166 characters. A 23,000-token social call cannot be explained by the system prompt alone. The user payload is the bulk. Missing instrumentation: a per-section token log on the assembled messages.
4. Same facts, multiple formats. The turn-33 persisted renderer inputs name `sergeant_mara` from interaction context, continuity, the narrative plan, the route, and referent tracking. That shows duplicate representation in session state. It does not assign a token count.
5. Retries resend the full context. Each retry input is the previous strict-social input plus 2,986, 3,421, and 2,933 tokens. That increment fits a retry instruction plus the rejected draft. The original prompt is sent again. It is not a small delta.
6. Failed validation causes the extra call. The retry purpose is `retry_escalation`, and turn-33 metadata records `model_retry_attempt` 1 with `hard_valid` false on the first narration. The safe line is what the player saw.
7. Context grew, modestly. Interpretation moved from 1,704 to about 1,930 and then stayed flat. Strict-social input moved from 22,783 to 25,090 across the conversation. Growth is real and is not the main cost. The main cost is the size of a single social prompt.
8. Large prompts were used for simple questions. Turns 3, 5, and 10 are ordinary NPC questions. Turns 1, 2, 6, and 9 are also simple and stayed at the interpretation size because they never entered narration.
9. Discarded outputs. The strict-social and retry outputs on turns 3, 5, and 10 were discarded. Combined discarded-call input: 22,783+25,769+24,442+27,863+25,090+28,023 = 153,970 input tokens, plus 524 output tokens. Turn 4's strict-social output was kept.
10. Reusable results. Once speech authority is `none` and no topic was selected, the safe line is determined. The narration call cannot add an authorized fact. Turn 7 already shows the skip when an authored fact exists. The knowledge-gap turns do not use that skip.

No section-level breakdown is reported as a measured fact. A bounded reading, labeled as a bound and not a measurement: the system prompt is a few thousand tokens at most, and the remaining roughly 20,000 tokens of each social call are the JSON payload. Instrumentation that would close the gap is a log of token counts for system prompt, rules, world, NPC, scene, history, contract, and retry addendum, taken where `game/gm.py` builds the two messages.
