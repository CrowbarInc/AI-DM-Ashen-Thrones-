# PR-PLAY-31 purpose-aware routing
Confirmed root cause: the router matches destination prepositions without first separating infinitive purpose. In the original text its only recognized destination preposition is the purpose's “to”; greedy tail capture yields “investigate the muddy footprints”. The reported last-match loop is present, but is not a general last-preposition parser: its anchored greedy expression can consume the whole remainder. Bare “northwest of the crates” previously has no destination-preposition match.

Repair: a finite verb vocabulary splits movement from “to”, “in order to”, or “so as to” purpose. Existing destination extraction then runs on the movement clause, with a bounded bare-movement fallback. Nested location descriptions retain their prepositions. Purpose is preserved in secondary_intentions, not executed. _analyze_clause also exposes it separately. inspect, examine, investigate, look for, search for and check are recognized; existing investigation target/discovery authority remains in the bridge and resolver. Search wording describes an attempt, not a guaranteed find.

Corrected destination: `northwest of the crates`. Purpose: `investigate the muddy footprints`.

Generalization: 12 parsing cases cover market/buy, guard/ask, gate/speak, road/investigate smoke, wagon/inspect wheels, original command, nested locations, alternative destinations, another purpose preposition, unrelated rest purpose, and no purpose. Six inspection cue cases pass. Local approaches with “to ask” and “to investigate” retain PR-PLAY-23's authored same-scene checks and execute no movement.

Files: game/conversational_orchestration.py, route_authority.py, player_interpretation_bridge.py, local_interaction.py, api.py, api_turn_support.py; tools/playtest/overlays.py and investigation_overlay_authority.py; tests/test_pr_play_31_purpose_routing.py.

Limits: finite purpose vocabulary; no general grammar, coordinate solver, clue semantic equivalence, multi-action execution, or physical target lookup across scenes. Unknown purpose verbs may still require clarification. Existing compound-action confirmation remains for separate consequential clauses. No provider call, model change, retry path, or planner was added.
