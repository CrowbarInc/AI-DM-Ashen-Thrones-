# Prioritized Optimization Plan

Optimization here means more useful gameplay publications per token and per second. A cheaper call that only produces refusals is not an improvement. No candidate is implemented in AT-OPT-01.

| Priority | Candidate | Evidence | Expected benefit | Quality and authority risk | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Do not call `gm.call_gpt` for an unresolved fast-path retreat the physical module already recognizes | F3: 23,377 tokens, output replaced, retreat not narrated. F: same sentence, 72 tokens, accepted. `physical_adjudication._operation` already maps “step back” to `retreat`. Expression-disable does not block `call_gpt` | About 23,000 input tokens and about 5.3 s of provider latency avoided on this utterance. When the physical experiment is on, the 72-token expression path remains | If the experiment stays off, the player gets the existing host or refusal sentence instead of a free-form narration. The one measured narration of this sentence was replaced. Do not turn position mutation on by default | High for the cost. Medium for wording quality on other physical verbs |
| 2 | Keep primary-narration retries off unless the first completion is known to be usable | 79 sent two `retry_escalation` calls, 57,075 input tokens, and published no narration. F3’s retry was disabled and correctly unsent, while the session counter still incremented | Up to ~29,000 tokens per avoided retry on the 79 prompt size. Unknown on later cycles that already set `ASHEN_DISABLE_PROVIDER_RETRIES` | A useful second narration never runs. 79’s published-narration count was already 0 | High on 79’s token share. Low that retries would have become useful without a prompt change |
| 3 | Wire the stated verification budget into the existing pre-dispatch ceilings | F3 script set 100,000 / 200,000. Admission compares the estimate before dispatch. Reconstructed estimate 28,031 against a 3,000 ceiling would refuse | Stops a verification cycle from spending a 23,000-token call. Does not shrink a legitimate opening | A 3,000 production cap would refuse every recorded opening (25,294 input). Limit this to verification harnesses | High that the current controller would refuse. The captured estimate itself was not logged |
| 4 | Record estimate, section byte sizes, sent-versus-counted calls, and whether the provider text was the published text | F3 ledger has tokens and latency and no prompt. Session `narration_provider_calls` is 2 while `sent` completions are 1. Route metadata on the saved GM object says `retry_escalation` for a `primary_turn` spend | Makes the next prompt cut measurable. No token saving by itself | None if the log stays free of prompt text and secrets | High that the gap is real |
| 5 | Shrink duplicated policy inside the primary payload | Reconstructed `response_policy` 21,657 bytes plus `turn_packet.response_policy` 6,037 bytes. Instructions 12,614 bytes. Recent log 402 bytes | Unknown in tokens. A byte cut is not a token cut until a captured request is re-measured | High. Those sections carry grounding, authority, and anti-leak rules. Deleting them can increase rejections, which raises tokens per useful publication | Medium that overlap exists. Low that a safe cut is known |

## What not to treat as the next cut

Conversation history is bounded to eight log entries and was 402 reconstructed bytes here. Bounding it further does not address the 22,777-token call.

Expression and contract interpretation are already the inexpensive routes: about 115–350 tokens and about 1,000–2,700 tokens in the live ledgers, against about 23,000–29,000 for primary and retry. The gain is staying on those routes when they already own the sentence.

Identical 25,294 input counts across openings are not, by themselves, proof of a duplicate dispatch. 79A sent two such completions with different output counts. Investigate only if a later ledger records two attempt ids for one player turn.

## Recommended experiment

**Name:** Unresolved retreat must not enter primary narration, and a 3,000-token verification ceiling must refuse before dispatch.

**Problem:** “I step back from the notice board.” with interpretation off, expression off, and the physical experiment off was classified `unresolved` and sent to `gm.call_gpt`. Cost 22,777 / 600 tokens. The publication was a replaced fallback. The same sentence with the existing physical and expression path cost 72 tokens and was accepted. The cycle’s 3,000-token budget was never written into admission.

**Boundary:** One guard in the existing skip path (`narration_skip` / `deterministic_provider_skip_line`). If the fast-path operation is `unresolved` and `physical_adjudication._operation` returns `retreat`, do not call `gm.call_gpt`. When the physical experiment is already enabled, leave the current `commit_physical` plus one expression attempt in place. When it is disabled, return the existing non-mutating host or refusal sentence. Do not enable the experiment by default. Do not mutate position. Do not edit prompts, models, or schemas.

The verification assertion is separate code only in the test: set `ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT=3000`, build a primary-sized message, and assert `admit_request` refuses with `sent` false. Production openings stay on their current ceilings.

**Owners:** `game/publication_contract.py`, `game/api.py` (`deterministic_provider_skip_line`), `game/physical_adjudication.py` (`_operation` only as a read), `game/provider_budget.py` and `game/gm.py` for the ceiling assertion. Tests under `tests/` for this guard only.

**Expected measurement:** The retreat fixture sends 0 provider requests with the experiment off and expression off. With a fake expression transport and the experiment on, it still allows one expression-sized call and no `primary_turn`. The ceiling fixture refuses a primary-sized estimate before dispatch.

**Risk:** Other unmatched physical sentences keep today’s primary path. A retreat with the experiment off loses free-form narration of that sentence. The measured free-form result was not a usable retreat narration.

**Acceptance:**

- Provider-free. No live call, no opening, no campaign rewrite.
- Retreat + unresolved fast path + expression disabled + physical gate off → 0 requests, pointer behavior matches the existing non-mutation rule.
- Physical gate on + fake expression transport → at most one expression call, no `gm.call_gpt`.
- Discover-clue skip and the operational request-ceiling refusal stay as they are.
- A non-retreat unresolved utterance can still reach primary narration when the ceiling allows it.
- Estimate over the 3,000 verification ceiling refuses before dispatch.

**Rollback:** Remove the guard if a held-out retreat loses a useful published narration that the host sentence cannot replace, or if the guard skips primary narration for a sentence `_operation` mislabels.

**Verification:** The new focused tests only. No historical suite, no live provider, no ATGB run.

Do not start this experiment automatically.
