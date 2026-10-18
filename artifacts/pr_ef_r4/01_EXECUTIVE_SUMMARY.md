# 01 — Executive Summary

PR-EF-R4 consolidates conversational authorization onto one grounding decision, `assess_addressee_grounding`, and records that decision on the resolution contract and on clarification responses. Provider-suggested NPC ids are candidates. They do not authorize an unresolved or non-unique person reference, and they do not advance the world while clarification is required.

## Implementation

The production path still interprets, then authorizes, then hands an eligible operation to the existing social, exploration, and movement resolvers. Authorization does not declare success. Final responses for an unresolved addressee use the authorization clarification. Narration is skipped only when a resolved social result has speech authority `none`, no revealed topic, no subjective allowance, and reply plan `consequential_information_request`.

## Critical findings

- The historical “I ask one of them what happened” failure does not execute and does not tick. Fresh live play with Sergeant Mara and Corporal Bren both visible asked which person was meant. Turn, clocks, and factions stayed put. The follow-up “The sergeant.” executed as Sergeant Mara.
- Explicit and uniquely grounded addresses still reach the social resolver. “I ask Sergeant Mara…”, “I ask the sergeant…”, “I ask the taller guard…” when height is actually written, and an in-conversation “What did you mean…” all executed the grounded NPC.
- A GM question about an NPC is not turned into NPC dialogue. “What does the sergeant know about the lantern?” stayed with the GM. “What did she mean by the road?” in the continuous conversation did not tick and did not open a new social exchange.
- Corrections, bare confirmation, and withdrawal do not execute a missing or already-resolved intention. The live correction after an executed ask said the action could not be undone and did not roll the turn back.
- Mixed and conditional intentions stay unexecuted until their condition or confirmation exists. The live conditional about the gate did not move. The following explicit walk through the courtyard gate did.

## Remaining defects

- One isolated live holdout, “What did you mean by the north road?” with only a session flag and no prior visible turn, was blocked as malformed communication. The same sentence succeeded as turn 3 of the continuous conversation.
- “I put the question to one of them” with one visible NPC clarified and did not mutate, but the spoken line was the provider’s clarification question rather than the authorization template.
- A knowledge-gap ask whose reply plan is `genuine_uncertainty` still calls strict-social narration and may retry. Live case B accepted “I don’t know.” after one format retry (50,784 input tokens). A clarified “what happened” ask whose plan said `authoritative_answer_available` while speech authority was `none` still spent a narration plus retry (51,910 input tokens) and then showed the safe line.
- The twenty PR-EF-R2 regression identities still fail. None were added and none were cleared.

## Recommendation

**B — PR-EF ACCEPTED WITH LIMITATIONS**

Core authorization, ambiguity, ownership, pending-intention, and resolver handoff behavior is demonstrated on fresh `/api/chat` output and on the frozen holdouts. The remaining gaps are a cold-follow-up interpretation block, clarification wording on one non-unique phrase, and narration cost when the reply plan is not the closed consequential-information plan. Do not start PR-EG from this package.
