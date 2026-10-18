# C22 implementation summary

The contract now carries the current commitment. New leaf module: `game/player_commitment.py`.

Primary versus secondary. A listen or watch phrase is supporting when it attends to an explicit ask/tell or to speech the player is receiving. It stays the primary operation when it has its own sensory target (`at the door`, `for footsteps`). Supporting sound is removed from the dimension set so the perception short-circuit cannot replace ASK. Independent perception still returns perceive. Two real perception intents keep the sound obligation on the inspect contract.

Modality. Sentences are executed now, intended later, conditional, hypothetical, or contemplated. Only executed-now text can select an authored exit, a travel recovery, or a physical open. `Then I'll go/head/walk/leave/travel/follow` is later. `Then I'll do the thing he said` stays a current act. `I inspect, then follow` stays the existing single committed action and is not marked hypothetical.

Unresolved addressee. A single generic role alias does not bind a nominal that adds an unknown title. Construction stores `requested_addressee` and `addressee_binding_status`. Speaker validation rejects a different NPC when that status is unresolved or ambiguous and no interlocutor is bound. The safe line says the addressed person cannot be identified. It does not name another NPC.

Unresolved travel narration. A travel resolution that did not transition is hard-invalid when the text asserts departure or arrival. The C18 seal then keeps the incomplete-action line. Successful committed exits still transition.

Files: `game/player_commitment.py`, `game/resolution_contract.py`, `game/interaction_completion.py`, `game/immutable_valid_response.py`, `game/scene_destination_binding.py`, `game/intent_parser.py`, `game/api.py`, `tests/test_pr_br_continuation22_commitment.py`, and the C21c milestone assertion that previously expected the bug.
