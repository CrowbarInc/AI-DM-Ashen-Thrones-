# Active interlocutor

`remember_interlocutor` records the minimum authoritative slot on the session:

- `bounded_improvisation.npc_focus` (stable id)
- `conversational_context.active_interlocutor` with npc id, scene id, campaign id, status, last player utterance, and last NPC response
- `conversational_context.recent_exchange`, capped at 6
- `interaction_context.active_interaction_target_id`

Provider prose is not stored as world truth. `focused_present_npc` returns that person only while the id is still in the current scene and the stamped campaign matches. A mismatch clears the focus.
