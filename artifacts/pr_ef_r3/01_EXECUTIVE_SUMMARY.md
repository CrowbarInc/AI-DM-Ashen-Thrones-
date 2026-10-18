# 01 — Executive Summary

**B — CONTRACT CONSOLIDATION. Stop before implementation and before PR-EG.**

The remaining failures are not four independent bugs, and they are not evidence that the resolvers or the simulation have to be replaced. They are repeated disagreements among records that all claim to know what the player meant.

The highest-priority case, "I ask one of them what happened," became an executed question to Sergeant Mara. The lexical addressee binder had already recorded the phrase as unresolved (`proposal:not_a_person`, proposed interlocutor "one of them"). After live interpretation was accepted, `establish_ordinary_gameplay_contract` replaced that binding with the provider's `sergeant_mara` id, set `ambiguous` to false, and the social resolver treated the id as an explicit target. `chat` then advanced the turn counter, the time-pressure clock, and every faction's pressure and agenda. Final validation rejected the invented narration and emitted the stock line in Mara's voice. It did not, and could not, undo the tick: the plurality flag was already gone.

That override still happens when a second visible NPC is added. The bridge accepts the provider id whenever `unresolved_references` is empty. The same function rejects the record if "one of them" is actually listed as unresolved. The safety check exists. The production path does not feed it the ambiguity the lexical layer already found.

A fresh interpretation of the same sentence, with Sergeant Mara and Corporal Bren both in the courtyard, did not name Mara. It also did not mark the referent unresolved. It labeled the turn GM/QUESTION with an empty evidence list, and orchestration answered as the GM instead of asking who "one of them" is. The historical sample executed a guess. The new sample refused to choose and still failed to clarify. Both samples are the same missing authorization bit.

The other three holdouts fail at the same seam:

- "I ask the sergeant who owns the lantern" was labeled GM/QUESTION while also carrying ASK `sergeant_mara`. Recipient won. The ask was discarded. The GM path answered from empty evidence: "That has not been established."
- "What does she mean by the road?" was blocked as legacy CLARIFICATION, then the blocked record was still answered by joining the last NPC line to a cause-not-established template.
- "Instead, make that a question about the lamp" had no pending intention to revise. The provider called it CLARIFICATION rather than CORRECTION, and the GM path answered with the visible lantern sentence.

Ordinary dialogue is expensive for a related reason. In the preserved eleven-turn conversation, 197,112 of 199,502 tokens were input. Ten interpretation calls used 19,277 input tokens. Four strict-social narration calls used 96,180. Three retries used 81,655 and resent the full prompt plus about 3,000 extra tokens each. Three of those narration pairs were thrown away. The player saw "I cannot answer that from what is settled here." The social resolver had already set speech authority to none, and the grounded-information mode does not open the existing bounded-improvisation lane. The model is asked to invent a reply, forbidden to invent a fact, and then replaced by a template.

Recommendation: keep the social, exploration, travel, and combat resolvers, the world tick, and final-response validation. Give them one authorization record that states addressee status, communication owner, and whether the turn may execute or advance time. Do not let a later stage replace an unresolved addressee with a model-chosen id, and do not let a recipient label throw away a contradictory direct address. Do not start a new router, a prompt rewrite, or PR-EG from this cycle.
