# 14 — Second Live Qualification

Source: `artifacts/pr_eg_r1/live_qualification.json`, key `second`.

Wording and order differ from the fifteen-turn script and from the historical PR-EG lines. Expectations were frozen in `tests/fixtures/pr_eg_r1_live_expectations.json` before execution and were not changed after the provider responded.

Frozen failures: 0.

Totals: 12 turns, 4 provider calls, 2 narration calls, 0 retries, 53,374 input tokens, 543 output tokens.

| Turn | Player | Response | Calls |
| --- | --- | --- | ---: |
| 1 | What can I see from here? | Courtyard description. | 0 |
| 2 | Sergeant Mara, is there a name for the road past the barred gate? | North road. | 1 |
| 3 | Sorry, what was that name? | Quotes the north road. | 0 |
| 4 | Do you like the quiet of morning better than evening? | "I prefer the evening." | 1 |
| 5 | You'd pick the same if I asked again? | Quotes the evening preference. | 0 |
| 6 | Has the lantern's maker ever been named? | "I couldn't tell you." | 1 |
| 7 | I was asking about the road's name, not the lantern. | Quotes the north road. | 0 |
| 8 | If I take a message to the gate for you, will you promise me something for it? | Declines a reward. No payment. | 0 |
| 9 | I look closely at the lantern. | Maker's mark. | 1 |
| 10 | I head through the courtyard gate. | Arrival on the street. | 0 |
| 11 | Back in the courtyard you named a road. What was it? | Mara is not here. Quotes the north road. | 0 |
| 12 | GM, repeat what Mara said about that road. | GM quotes the north road. | 0 |

## Scores

- Behavioral: the frozen checks pass, and each reply addresses the turn's intent.
- Ownership: NPC lines stay with Mara while she is present. Turns 11 and 12 are GM speech.
- Continuity: the road name survives a failed maker question, a preference, and a scene change.
- Naturalness: declines and uncertainty are plain. Quotes use "I meant this:" or "said:".
- State: no reward, no password, no faction change from talk. Inspection and movement use their resolvers.
- Provider: two narrations for the new street fact and the preference. Every follow-up is local.
