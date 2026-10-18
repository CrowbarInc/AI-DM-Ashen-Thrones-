# 11 — Provider Efficiency

## Historical follow-up

"What did you mean by that?" after the north-road answer.

The engine did not have the delivered sentence as the answer. Strict-social narration ran, failed, and retried. About 52,957 input tokens produced "I couldn't tell you."

## Final call graph for that turn

Interpretation: not called. The continuity ask is deterministic.
Narration: skipped. Dialogue authority sets the quote and `reuse_prior_speech`, so `social_narration_unnecessary` is true.
Retry: none.
Player-facing text quotes the north road.
Input tokens: 0.

## Fifteen-turn totals

| | Calls | Narration | Retries | Input tokens |
| --- | ---: | ---: | ---: | ---: |
| Historical single follow-up | narration + retry | 1 | 1 | ~52,957 |
| Final 15-turn conversation | 6 | 2 | 0 | 56,440 |
| Final 12-turn second conversation | 4 | 2 | 0 | 53,374 |

The two narration calls in each conversation are the first street-name answer and the preference. Each is one call, about 24,000–26,000 input tokens, and neither retried. That size is the existing strict-social prompt. This cycle did not rewrite prompt compression.

Follow-ups, corrections, promise declines, the absent-NPC recall, and the GM recall are zero-call turns.

Unknown maker questions use one interpretation call and a determined "I couldn't tell you." They do not narrate.

## Why a retry is no longer used to recover context

The quote is already in session state. A second narration cannot add the missing referent, so it is not started.
