# 14 State continuity

The provider-disabled control and the live session were compared after the same four actions.

Matching fields: scene `frontier_gate`, visited scenes, player id, HP, inventory, equipment, discovered clues, scene flags, NPC runtime, quest journal, conditions, combat, world flags, and clocks.

The campaign run ids differ because each seed creates a new id. That difference is the isolation boundary, not a narration edit.

Discovered clues in both finals:

"The missing patrol was last seen taking the northwest mud track past the crates."

There is one copy. Combat stayed inactive. HP stayed 8/8. No inventory field was added by narration.

NPC runtime is created by the turn itself with attitude, trust, fear, and suspicion at 0. The live and control records match. The failure-injection before/after NPC flag is false because that comparison starts from the seed, before the turn creates the runtime record. It is not a change caused by the rejected death sentence.

Narration is applied after `save_session`. The saved authority does not take the candidate as an instruction.
