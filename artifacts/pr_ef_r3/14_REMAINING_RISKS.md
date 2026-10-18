# 14 — Remaining Risks

Unresolved:

- Provider stability. One fresh sample of "one of them" with two NPCs chose GM and a null target. The historical sample chose NPC and Mara. A larger sample was not collected. The recommendation does not depend on either shape, and it has not been measured across dozens of paraphrases.
- Section-level token shares inside the 23,000-token social payload. Payloads were not stored. The purpose totals and the retry deltas are measured. The claim that the user payload dominates the system prompt is a bound from the current prompt's character count, not a tokenizer dump of the historical request.
- Whether players prefer a clarification when only one person is in the scene. The invariant chosen here clarifies anyway. That may feel pedantic in play. It is the stated invariant. It can be relaxed later only by an explicit uniqueness rule, not by another silent id.
- Bounded incidental color. The report says the record must be able to express it. It does not say the wording will be good, and it does not authorize implementation.
- The twenty inherited regression failures from R2. They were not re-run or reclassified. Scaffold leakage and repeated interruptions may be independent.
- Case C's product choice. The prompt says "what did they mean" is a GM question. The holdout expected an NPC question. The concatenation bug is independent of that choice. The choice itself is still open.
- Full `/api/chat` was not repeated for the fresh probes. Authorization was replayed in process. A future implementation still needs one disposable HTTP conversation before anyone calls it qualified.
- Default timeout in this cycle was 45 seconds. R2's live runs used 25. No timeout was hit on the ten short interpretation calls.

Provider limits. The model does not reliably emit `unresolved_references` or AMBIGUOUS for plural address. Temperature was 0 on these calls and the two samples still differed. Engine checks have to be independent of that field.

Regression risk of the future change. The R2 identity carry is load-bearing for "known NPC stays known." An implementation that ignores bridge ids entirely will bring back "the person cannot be identified" for ordinary named asks. The rule is narrower: the bridge id loses only when the lexical addressee is an explicit non-unique person or the owner fields conflict.

Playability risk if nothing is done. A plural address can spend a turn and move every faction. A direct question to an NPC can be answered by the GM with a policy sentence. Corrections can be answered with scenery. Knowledge-gap talk costs on the order of 50,000 input tokens to show one template sentence. Those are enough to make ordinary human playtesting untrustworthy. They are not enough to justify replacing the simulation.
