# 13 — Fallback and Retry Audit

PR-EG-R5 · 2026-10-17 · investigation only

| Trigger | Current player-facing outcome | Context retention / loop | Provider exposure |
|---|---|---|---|
| No knowledge | NPC inability or generated uncertainty | speaker often preserved; requested relation may be lost | optional expression, legacy strict-social if no determined speech |
| Missing reference | which person/subject/earlier statement | pending choices retained; false ambiguity can loop | deterministic or one interpretation |
| Conflicting authority | adopted GM safe_nonresolution | speech integrity preserved; semantic question unresolved | may follow narration/retry |
| Expression invalid | original host proposition/fallback | retains its source, including wrong selected preference | one expression attempt, no local expression retry |
| Unsupported operation | cannot carry out / no action attempted | operation framing can discard a reasonable conversational question | interpretation may already be paid |
| Missing adoption | complete authorization before delivery | preserves R4-R1 integrity boundary | no added call just to seal |
| Provider malformed/failure | blocked interpretation or safe host fallback | no guessed target; generic wording may end conversation | budget/timeout bounded |
| Strict-social failure | gm_retry repairs, escalation, terminal fallback | may reinforce wrong speaker/selected topic | historical chain reaches three large calls |
| Historical correction/overlap | repeat prior answer | zero-cost dead-end loop | often zero calls |

Sources: [game/gm_retry.py:1249](../../game/gm_retry.py#L1249), [game/gm_retry.py:2746](../../game/gm_retry.py#L2746), [game/expressive_dialogue.py:873](../../game/expressive_dialogue.py#L873), [game/immutable_valid_response.py:1491](../../game/immutable_valid_response.py#L1491), [game/api_turn_support.py:601](../../game/api_turn_support.py#L601), [game/provider_budget.py:1](../../game/provider_budget.py#L1).

Loops are mostly across turns rather than unbounded recursion: correction → old quote → player correction → old quote; unresolved addressee → pending state → failure to match natural-language resolution → same clarification. Escalation is a distinct within-turn cost chain. R4 playful11 spends 81,078 input tokens over strict-social and two escalation calls and still uses Mara for a Runner request. A cheaper wrong deterministic answer is still unplayable. Recommend a single scoped fallback after the normal semantic attempt: acknowledge the unresolved question, retain the resolved references, and request only a genuine missing slot. Do not modify fallbacks in R5.
