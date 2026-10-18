# 12 — Architectural Options

## Option A — Localized repair

Patch each failure where it now breaks.

- In `establish_ordinary_gameplay_contract`, do not overwrite `proposal:not_a_person` with a bridge id.
- In `_communication_decision`, if the player explicitly asks a named NPC, do not answer as the GM.
- Delete or narrow the cause-template suffix.
- Treat a leading "Instead" as correction, and require a pending object for ordinary asks.

Scope is a few branches in two modules. Complexity is low. Regression risk is high in a different way: R2's identity carry is the branch that would be narrowed, and that carry is what fixed "the sergeant cannot be identified." A narrow guard can miss the next phrasing. The fresh two-NPC sample never produced `proposal:not_a_person` as the winning record, because the provider called the turn a GM question with a null target. A bridge-only patch would not have changed that sample. The cause suffix is the one change that is truly local. The other three will recur wherever recipient, unresolved refs, and the lexical person disagree.

Performance does not improve under A unless a separate change skips narration when authority is `none`. That skip is easy to bolt on and easy to get wrong if it is not tied to the same eligibility bit.

## Option B — Contract consolidation

Keep resolvers, simulation, persistence, and final-response validation. Stop letting them each decide the player's meaning.

One authorization record, produced after interpretation and lexical grounding and before resolver selection or the world tick:

- Addressee status: resolved, unresolved, ambiguous, or not applicable, plus the id only when resolved.
- Communication owner and speech-act purpose, copied from the interpretation and not rewritten to ACTION merely because an ASK will execute.
- Execution eligibility and mutation eligibility.
- The operation the resolver is allowed to run.

Rules that the current code can enforce without a new pipeline:

- A model id does not resolve an explicit non-unique person when more than one person is visible. One visible person may be named in the clarification. The turn still does not execute.
- Recipient and a contradictory direct-address operation are a conflict, not a silent winner.
- A blocked interpretation is not re-answered by joining evidence unless the authorization record says the turn is a GM question with selected evidence.
- `chat` ticks only when mutation eligibility is true.
- Narration and `safe_nonresolution` consume the bound speaker. They do not acquire one.
- When the record says there is no canonical answer, skip the narration call and either speak a visible partial or the safe line. Incidental color, if allowed, is marked non-persisted and is not a new topic.

This fits the existing contract object. `establish_ordinary_gameplay_contract` already claims to be the one contract. The work is to make the other stages consume it and to stop the bridge id, the recipient, and the tick from outranking it. No second interpreter. No new router module.

Generalization is better than A because the fresh sample and the historical sample fail differently and would both be caught by "no resolved addressee, no tick" and "owner conflict is explicit." Regression risk is real and is limited to the seam. Authored-topic answers, movement, and inspection skips stay on their current resolvers. The risk to manage is an overly strict addressee rule that clarifies when the player named the only visible person clearly. The rule above does not do that. "I ask Sergeant Mara" remains eligible. That was confirmed on the fresh explicit probe.

## Option C — Architectural redesign

Replace the conversational orchestration: interpretation schema, communication decision, contract constructor, and the way narration is prompted.

What would be retired: the dual recipient-plus-operation record, the blocked-record redecision, and the bridge override. What would be preserved: social, exploration, travel, and combat resolvers; world progression; storage; final-validation rejection of invented canon; provider budget and the one-retry ceiling.

Nothing in the evidence says those resolvers cannot express the required behavior. Turn 7 and turn 11 already do. A redesign would rebuild the seam that Option B tightens, at the cost of revalidating every path EF through R2 just made pass. Migration risk is a second orchestration living beside the first, which is how the current disagreements were created. Expected benefit beyond B is a cleaner prompt and a smaller narration payload. That benefit is real and can be taken inside B by not calling narration for a determined safe line. It does not require replacement.

Option C is not recommended. It is cleaner as a diagram. The failures are at the points where existing records disagree, and those records can be made to agree.

## Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Conversational correctness | Fixes the captured sentences that match the patch | Covers both the executed guess and the fresh GM non-clarification | Would also cover them, after a rewrite |
| Semantic generalization | Low. Fresh sample bypasses the lexical patch | The eligibility bit does not depend on one provider shape | High in theory, unproven |
| Authority integrity | Leaves recipient, purpose, and tick as separate authorities | One record before the tick | New authority, old one must be removed completely |
| State integrity | Case A only, if the patch sees the lexical result | Tick gated on the record | Same, if the new path remembers to gate the tick |
| NPC dialogue quality | Unchanged unless the safe-line skip is added ad hoc | Skip, or a marked incidental lane | Same opportunity, larger change |
| Bounded improvisation | Not connected | Uses the existing proposal type only when the record allows non-persisted color | Easy to redraw, easy to over-widen |
| Provider efficiency | Unchanged | Drops the determined-failure narration and its retry | Might also shrink prompts; not required to do so |
| Complexity | Small | Moderate, one seam | Large |
| Regression risk | High for the R2 identity fix if the guard is broad | Moderate, seam only, resolvers untouched | High. Reopens passed conversations |
| Maintainability | Next cycle patches the next field | One place to read eligibility | Two generations during migration |
| Future features | Each new act adds another override | New acts set the same bits | New orchestrator must relearn resolvers |
| Ordinary playtesting | The four sentences may pass and the next paraphrase may not | The invariant is testable without a phrase list | Delayed by the rewrite |

Evidence versus prediction. Evidence: the override, the recipient win, the blocked-record redecision, the tick, the discarded narration, and the two different provider shapes for the same plural sentence. Prediction: that a single eligibility bit will generalize to paraphrases not in the probe list. That prediction is bounded by the probes that were run. It is not a claim of universal competence.
