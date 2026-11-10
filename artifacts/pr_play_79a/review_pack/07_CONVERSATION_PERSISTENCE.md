# Conversation persistence

Development tests cover continuation inside a session, continuation after look/wait, goodbye and "I end the conversation", scene departure, NPC relocation, campaign-id mismatch, and `storage.save_session` / `load_session`.

The live HTTP snapshots restored scene, campaign id, focus, interlocutor slot, and flags for both campaigns. The resumed conversation line was another "Who are you?", which the provider answered as the Gate Guard.
