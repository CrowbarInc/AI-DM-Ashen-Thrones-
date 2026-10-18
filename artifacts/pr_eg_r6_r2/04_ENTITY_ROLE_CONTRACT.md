# 04 Entity-Role Contract

Entity roles: speaker, addressee, mentioned_npc, requested_subject/object, information_source, prior_proposition, correction_target. IDs must exist in scene participants and have literal utterance witnesses. Non-NPC concepts do not acquire canonical IDs. Grounding verifies identity and witnesses; it cannot prove every proposed role assignment semantically. game/unified_semantic_planning.py:404 (def _proposal_schema); game/unified_semantic_planning.py:817 (def authorize_information_turn).
