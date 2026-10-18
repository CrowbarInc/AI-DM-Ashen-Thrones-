# 05 — Historical Failure Traces

PR-EG-R5 · 2026-10-17 · investigation only

All trace identities and complete retained metadata are in [historical_trace_extracts.json](historical_trace_extracts.json). “First” below means earliest demonstrable retained decision, not an invented missing intermediate trace.

## A. Harbor coordination → bell

Evidence: **R4 B_skeptical 1**. The player asks who decides ferry docking and departure. First observed incorrect selection is social.topic_revealed=bell with requested_information=general and answer_sufficiency=directly_answers. There is no provider interpretation in this turn; expression is downstream. Lexical subject overlap and permissive general support admit the bell; the sealed sentence faithfully discloses it. The safeguard tests authorization of an owned fact, not answer relevance. Smallest boundary: require source evidence to cover the requested relation before host disclosure adoption.

## B. Correction → replay

Evidence: **R4 B_skeptical 2 and 7**. The player explicitly rejects the bell answer and asks who manages schedules. The first recorded wrong decision is conversational_topic_correction at turn 2, then repeat_delivered_statement at turn 7; neither invokes a provider. _FEELING matches “I was asking about” and returns the old quote; later overlap/repeat cues recover the very subject being rejected. A valid historical source cannot justify this response act. Smallest boundary: preserve correction target, rejected interpretation and replacement question before resolving a speech reference.

## C. Morning → evening

Evidence: **R4-R1 primary 5–6**. Turn 5 adopts authored preference=morning as established. remember_dialogue_commitment returns early for established posture; delivered history still contains the correct preference. At turn 6 _best_exchange can find that morning proposition, but continuity_directive returns an ASK. New authority has subject=time, no topic, no reusable commitment and no prior commitments. Host bounded_personal_line deterministically chooses evening from NPC-ID parity. Expression incidental_characterization is rejected, retaining this wrong fallback. First observed divergence is failure to carry the historical proposition into the new authority, before expression validation. Smallest boundary: make follow-up planning and fallback consume the same bound proposition regardless of authored/incidental origin.

## D. Named Mara → speaker clarification

Evidence: **R4-R1 primary 12; R4 A_cooperative 4**. Local replay of _best_exchange on the saved primary-12 state returns ambiguous although the name constrains its pool to Mara. Distinct gate-related propositions within that one speaker can tie on overlap; the caller renders ambiguity with _ambiguous_line over all rows, listing Mara and Runner. This is subject/proposition ambiguity falsely rendered as speaker ambiguity. R4 A_cooperative 4 separately retains proposed_target=sergeant_mara but emits ambiguous_addressee; the earlier history is implicated, but the complete internal grounding trace is unavailable. Do not assert the same mechanism for both. Smallest boundary: typed ambiguity containing candidate proposition IDs and already-resolved speaker, with no reopening of speaker identity.

## E. Casual speech → action treatment

Evidence: **R4 A_casual 14 and A_playful 4**. A_casual 14 explicitly says “Hey Sergeant Mara, just to be clear, I’m trying to talk with you” and asks about trouble/road traffic. The recorded deterministic reason is movement_question, giving an unavailable route to the remainder of the sentence. Earliest observed wrong decision is modality/destination recognition; no provider call occurs. In A_playful 4 the provider captures two ASK components accurately but labels recipient MIXED. Host _communication_decision maps MIXED to “settle the question before attempting the action” despite two speech requests. Both provider and host contribute; provider meaning is not presumed correct. Smallest boundary: distinguish multi-party speech from mixed speech plus consequential action.

## F. Playful input → expensive strict social

Evidence: **R4 A_playful 11; R4-R1 secondary 8**. R4 turn 11 requests a memorable traveler story from Runner while mentioning Mara. Stored operation is ASK targeting Mara; strict-social receives 25,817 input tokens, followed by two escalation calls at 28,430 and 26,831. Delivered speech still comes from Mara. The earliest retained defect is target selection; exact earlier branch internals are not retained, so long-input length is correlation, not proven trigger. Source supports fallback to legacy generation when host determined speech is unavailable, then retry failure recovery. Secondary-8 current predecessor evidence still selects the irrelevant bell and conflicting targets, but final adoption now retains a fixed GM inability. Smallest boundary: coherent semantic plan before narration, and a hard conversational provider budget with context-preserving no-retry fallback.

Source anchors: [game/social.py:1611](../../game/social.py#L1611); [game/conversational_continuity.py:582](../../game/conversational_continuity.py#L582); [game/conversational_continuity.py:318](../../game/conversational_continuity.py#L318); [game/dialogue_authority.py:628](../../game/dialogue_authority.py#L628); [game/conversational_orchestration.py:448](../../game/conversational_orchestration.py#L448); [game/gm_retry.py:1249](../../game/gm_retry.py#L1249). R4’s critical post-validation replacement is a historical delivery symptom repaired in R4-R1, not the explanation for every earlier irrelevant answer.
