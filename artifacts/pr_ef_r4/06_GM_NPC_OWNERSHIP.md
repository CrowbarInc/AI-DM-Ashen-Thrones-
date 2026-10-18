# 06 — GM/NPC Ownership

## Explicit NPC address

“I ask the sergeant who owns the lantern.” Fresh interpretation labeled the recipient GM and the purpose QUESTION. Grounding still treated the speech act as an executable address of Sergeant Mara. The social resolver ran for `sergeant_mara`. The GM label did not become the reply owner.

“I ask Sergeant Mara whether the north road is watched.” Live turn 2: interpretation plus one strict-social call, NPC `sergeant_mara`, authored north-road line.

## GM questions about an NPC

“What does the sergeant know about the lantern?” Live holdout: recipient GM, no social result, no mutation, no NPC “says” line.

“What did she mean by the road?” with an active interlocutor and a scripted ASK of Mara does not continue the exchange. A third-person question is not a second-person follow-up. The test `test_third_person_question_is_not_an_active_npc_continuation` covers that adversarial record.

Live conversation turn 4 used the same sentence after Mara had spoken. Kind `conversational_answer`. Turn, clocks, and factions did not change. The text quotes the prior public line (“Sergeant Mara says…”) and then repeats the established road fact. That quote made the automated scorer fail; the turn did not open a new social exchange and did not tick. `critical_unauthorized_mutation` is false.

## Continuation

Live turn 3, “What did you mean by the north road?”, continued Mara (`target_provenance` contextual, `established` relationship on the contract) and recalled the north-road line with interpretation only.

An isolated live holdout of that sentence, with the session flag set and no prior visible turn, returned `malformed_communication` (“I need you to clarify who you are addressing.”) and did not execute. The continuous conversation is the evidence that a real follow-up continues.
