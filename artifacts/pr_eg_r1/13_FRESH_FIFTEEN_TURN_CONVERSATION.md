# 13 — Fresh Fifteen-Turn Conversation

Source: `artifacts/pr_eg_r1/live_qualification.json`, key `primary`.

Route: `POST /api/chat?ui_mode=player`. Disposable campaign. Model route `gpt-4.1-mini`. Frozen checks in `tests/fixtures/pr_eg_r1_live_expectations.json` were not edited after the run. Frozen failures: 0.

Totals: 6 provider calls, 2 narration calls, 0 retries, 56,440 input tokens, 918 output tokens.

| Turn | Player | Response | Calls | In tokens | State |
| --- | --- | ---: | ---: | --- |
| 1 | Could you describe the courtyard? | GM courtyard description. Mara is visible. | 1 | 1,704 | no social |
| 2 | I ask Sergeant Mara what the street beyond the gate is called. | Mara mutters that it is the north road. Clue `north_road`. | 2 | 26,319 | social turn |
| 3 | What did you mean by that? | Mara quotes the north-road sentence. | 0 | 0 | no clock change |
| 4 | Say that again in plainer words. | Same quote, framed as "I meant this." | 0 | 0 | none |
| 5 | Do you prefer the morning or the evening? | "I prefer the evening." | 1 | 24,606 | social turn, topics unchanged |
| 6 | Why that one, then? | Quotes the evening preference. | 0 | 0 | none |
| 7 | What is the street called? | Quotes the north road again. | 0 | 0 | none |
| 8 | Who forged the lantern? | "I couldn't tell you." | 1 | 1,904 | no new fact |
| 9 | I meant the road, not how you feel. | Quotes the north road. No undo line. | 0 | 0 | executed action kept |
| 10 | Promise me a reward if I carry a message for you. | "I can't promise you a reward for that." | 0 | 0 | no obligation |
| 11 | Swear you'll pay me ten silver if I do it. | Same decline. No payment. | 0 | 0 | no silver |
| 12 | I inspect the courtyard lantern. | Maker's mark. Clue `lantern_mark`. | 1 | 1,907 | inspection |
| 13 | I walk through the courtyard gate. | Arrival on the waystation street. | 0 | 0 | scene change |
| 14 | Earlier you could not tell me who forged the lantern. Is that still where you stand? | Mara is not here. She could not answer that. | 0 | 0 | no remote speech |
| 15 | GM, what did she say the street was called? | GM quotes the north road. No "says,". | 0 | 0 | none |

## Playability

A player can follow the road name from the first answer through a preference, a correction, a refusal, a scene change, and a GM recall. The speaker stays Mara until she is absent. The weak spot is turn 4: the paraphrase is a verbatim quote, not plainer wording. The answer is still the right fact.
