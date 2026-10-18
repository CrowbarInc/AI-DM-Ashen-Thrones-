PR-DU State Ownership

Session ownership: game.api chat pipeline owns turn_counter/clocks for submitted chat turns; storage owns persistence.
World ownership: game.world advance/apply helpers and resolver outputs own world mutations.
Combat ownership: combat helpers; not exercised by PR-DU.
NPC runtime ownership: interaction_context/social systems initialize and update NPC runtime/addressability.
Conversation history ownership: storage.append_log.

Production/experimental difference:
Experimental DisposableHarness mutated in-memory session directly. Production activate_scene reloads persisted session, which exposed a bug: same-turn in-memory fields could be lost across scene transition. PR-DU repairs this by saving session before activate_scene reloads.
