# PR-CO Viability Report

Decision: **E — BUDGET EXHAUSTED**

The planned eight turns did not finish. Twelve provider requests were used by the end of turn 5's interpretation. Combined tokens were 295,037, under the 300,000 cap. The request cap is what stopped the run.

The five HTTP turns already show that ordinary play is not viable on this build. The budget result is the consequence of a rejection loop, not an absence of evidence. Turns 1–4 each generated a narration, failed hard validation, retried, failed again, and emitted a safe replacement. Mean score on the five completed turns is 5.8 / 10. Relevance and narrative quality are the weak dimensions. Authority of durable state held.

## What was played

One isolated session on the authored default frontier gate. Guard Captain, notice board, missing-patrol topic, faction clocks. Production `data/` was not written. Application code was not modified. Provider was OpenAI `gpt-4.1-mini` (`gpt-4.1-mini-2025-04-14`) through the official Responses API. Preflight was healthy and returned usage before gameplay calls.

| Turn | Intent | Final player text | Score |
| --- | --- | --- | ---: |
| 1 Preference | social / ask / guard_captain | Two authored banner sentences | 6 |
| 2 Follow-up | exploration / perceive | Inspection line about "the wear" | 3 |
| 3 Authored patrol fact | social / ask / guard_captain | Refusal, while the topic was stored | 5 |
| 4 Examine the notice board | exploration / inspect | No further reliable detail | 7 |
| 5 Describe the gate | exploration / perceive, generation blocked | Broken fallback from authored visible facts | 8 |
| 6 Wait | not sent | | |
| 7 Continuity | not sent | | |
| 8 Read the notice more closely | not sent | | |

## Token and latency summary

Measured:

- Input tokens: 290,627
- Output tokens: 4,410
- Cached input tokens: 0
- Total tokens: 295,037
- Mean tokens per completed HTTP turn: 59,002
- Median tokens per completed HTTP turn: 69,629
- Maximum tokens for one turn: 78,695 (turn 3)
- Retry token overhead: 161,822 (54.8%)
- Mean provider latency per request: 4.214 seconds
- Mean provider latency per completed turn: 9.605 seconds
- Estimated spend at published `gpt-4.1-mini` rates, no cache: input $0.1163, output $0.0071, about **$0.123**

Character-share estimates for turn 1's first generation (system message plus user JSON; not tokenizer counts) put mechanical resolution data at 33%, policy and authority instructions at 29%, and system/developer instructions at 16%. Conversation history was 1.5% because the log was still empty. The payload is large before the scene has a history.

## Viability by question

1. Natural-language comprehension: turn 1 and turn 3 social asks bound the captain. Turn 4 bound the notice board. Turn 5's interpreter proposed a gate description. Turn 2 did not keep the follow-up on the social subject.
2. Resolver selection: social on the two direct captain questions; exploration on the examination and the description. The follow-up was selected as exploration even though interpretation proposed `ask`.
3. NPC usefulness: the emitted captain never states a preference and, on turn 3, denies knowledge that the session has just recorded.
4. Exploration: the board is recognized and not inspectable in this default scene. The player is not told the authored posting that is already visible.
5. Passive waiting: not reached. Clocks did tick on every played turn, including operation-complete events on turn 5, without a spoken fight.
6. Narrative continuity: the spoken thread loses the preference immediately. The patrol fact exists in clue knowledge and is absent from the spoken answer.
7. Authority and state integrity: no hidden fact, NPC, item, or scene was invented into durable state. The gate is strict enough to discard both bad extras and the licensed topic sentence.
8. Player-facing quality: turns 1–4 are not answers a player can use. Turn 5 is a grounded but ungrammatical fallback.
9. Token consumption: about 59,000 tokens per completed turn, with more than half of all tokens spent on retries whose narrations were also rejected.
10. Latency: individual calls are a few seconds, except turn 4's 17-second retry. The practical cost is the second call, not a hung request.

## Earliest failing boundary

Turn 1 final emission. Resolver and addressee were already right. The model had answered. `safe_nonresolution` replaced that answer after `unauthorized_resolution_decision_fact`.

## Stop

Request 12 completed (turn 5 interpretation). The runner did not send a 13th call. No parallel session. No second model. No automatic rerun. No application repair.
