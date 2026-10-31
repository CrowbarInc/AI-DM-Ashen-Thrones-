# 04 — Evidence-Selection Analysis

## Contract classification

**C — Permitted without meaningful positive guidance for this case.** The schema requires an array, not a nonempty array (`live_chat_interpretation.py:44–46`). `valid_communication:65–75` checks that every supplied ref exists; `all(...)` accepts an empty list. No mode requires an empty list. The system's “Select evidence_refs only when the supplied PUBLIC passage actually answers the question” is useful negative relevance guidance, but does not require selecting relevant passages for a corrected implicit question. “No evidence means unknown” does not distinguish unknown facts from an acknowledgment needing no facts. Therefore A is false; B overstates a positive discouragement absent here. Relative to the expected product behavior the outcome is inadequate, but [] is not formally forbidden, so D is not the schema classification. The reason the model chose [] rather than another allowed value remains internally indeterminate.

## Construction, availability, authorization and sufficiency

`public_conversation_evidence` at `conversational_orchestration.py:308–341` constructs stable-in-this-request string keys: scene, visible:<index>, reply:<index>, optional cause:reply:<index>, npc_latest_reply, npc:<speaker>:<topic>. Visible indices are positional, not durable referent identities. They may be selected only against the supplied dictionary. Entity catalog IDs are a separate namespace and do not automatically authorize answer text.

For L1/L2, the function's return **and the actual saved request user message** contain visible:1, visible:2, visible:3 and full reply:0. For L3 the request message independently confirms the same passages, even without a separately traced evidence-builder return. Its before-state visible_facts agree. The three passages describe the gate serjeant, tavern runner, watchers/refugees; all had already been emitted in the prior turn. Thus availability, relevance, player access and disclosure authorization are each verified independently of merely seeing identifiers. They suffice to answer “describe the people in front of me” but not to expose secret identities or motives.

Scene and notice-board/census passages are public yet weaker answers to the narrowed subject. A full reply:0 would repeat unnecessary weather and notice text. Selecting visible:1–3 is a tighter response. More facts are not needed. Opening-seed and hidden scene facts are not silently added to the candidate set. This investigation does not promote hidden facts, unrevealed clues or every NPC topic to public knowledge.

## Projection and downstream effects

At `live_chat_interpretation.py:468–473`, the adapter record gets `public_evidence = {ref: evidence[ref] for ref in communication.evidence_refs}`. Empty selection therefore removes all available passages from the record's answer projection. It does not mean the passages were unavailable to the model.

`_communication_decision:573–581` treats purpose CLARIFICATION plus empty projected evidence as a clarification question. With selected evidence, INTERPRETED status and no unresolved reference, that particular clarification arm would not fire, and the else arm could return evidence. That is a source-derived counterfactual, **not a tested live result**. The earlier legacy eligibility still labels mode CLARIFICATION as NEEDS_CLARIFICATION, but the API record reconsideration allows a conversational answer. Evidence-only changes therefore might alter the final response, yet leave the disposition contract contradictory and lose the distinction between an answer and a necessary clarification.

The host joins selected public passages at 583–586; it does not retrieve omitted passages on this route and does not independently assess whether an alternative passage could answer the corrected question. It also does not prove selected text semantically answers merely by validating identifier membership. Existing causal-question handling at 587–588 is a narrow distinction between an observed outcome and its cause, not a general answerability check.

## Necessary exceptions

A plain acknowledgment, conversation close, withdrawal receipt or legitimate request for missing parameters may correctly select no evidence. Tests of these must remain separate from requests to continue an answer using known information. The defect is this **answerable conversational correction** being represented as an unanswerable clarification, not the general legality of `[]`.

Disposition and evidence are co-produced in one completion. The trace cannot prove that CLARIFICATION caused the omission, that omission caused CLARIFICATION, or that one token-level decision preceded the other. Earliest supported failure is their joint interpretation result, followed by deterministic selection/projection consequences.
