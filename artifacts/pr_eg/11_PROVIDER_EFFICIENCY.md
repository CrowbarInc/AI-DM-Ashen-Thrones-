# 11 — Provider Efficiency

## Call graph

Unchanged shape: interpretation when live interpretation is on, then at most one strict-social narration, then at most one retry.

New skips:

- Narration is not requested when `dialogue_authority.narration_determined` is true, incidental speech is off, and speech authority is none. The player line is the determined sentence.
- A retry is not requested when a harmless quoted remark can be validated on its own.

Narration is still requested for a sufficient authored topic and for a belief or opinion question.

## Before and after, same twelve-turn script

The first fresh run is `live_qualification_before_quote_recovery.json`. The final run is `live_qualification.json`. Model `gpt-4.1-mini-2025-04-14`. Wall clock about 45 seconds each.

| Turn | Before | After |
| --- | --- | --- |
| Street name | 2 calls, 0 retry, 26,258 in | 2 calls, 0 retry, 26,258 in |
| “What did you mean?” | 1 call, 0 retry, 1,981 in, repeated the road name | 3 calls, 1 retry, 52,957 in, “I couldn’t tell you.” |
| Who forged the lantern | 1 call, 0 narration, 1,981 in | 1 call, 0 narration, 1,965 in |
| What troubles you | 3 calls, 1 retry, 54,871 in, “I couldn’t tell you.” | 2 calls, 0 retry, 26,791 in, “It’s this watch, mostly.” |
| Morning or evening | 3 calls, 1 retry, 53,879 in, “I couldn’t tell you.” | 2 calls, 0 retry, 26,291 in, “I do not know enough to answer that.” |
| Password | 1 call, 0 narration, 1,883 in | 1 call, 0 narration, 1,892 in |
| Whole conversation | retries on turns 6 and 7 | one retry, on turn 3 |

Final conversation: 16 provider calls, 145,400 input tokens. The historical single lantern question was about 50,784 input tokens. That question is now under 2,000.

Turn 3 moved the wrong way between the two fresh runs. The first run reused the authored road line without narration. The second run generated, failed validation, retried, and fell back. That is live routing variance plus a fallback that does not restore the topic the player just heard. It is not an improvement.

## Target

Ordinary NPC questions were aimed at one interpretation call and at most one dialogue call. Determined gaps meet that (interpretation only). The street name and the trouble question meet one narration and no retry, at about 26,000 input tokens each. The follow-up “what did you mean” missed the target. The preference question used its one narration to produce ignorance.

Skipping narration for every general unknown was tried and reverted. It skipped calls that speaker-repair and prompt-contract tests require, and it made “who attacked them?” determined. The skip stays on the listed specific kinds.
