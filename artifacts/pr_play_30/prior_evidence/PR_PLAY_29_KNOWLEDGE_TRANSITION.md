# PR-PLAY-29 knowledge transition

Verdict: PASS, PUBLIC_FACT -> AUTHORED_TOPIC.

Turn 1 selected scene:frontier_gate:visible:2, own_offerings attributed to tavern_runner; authorized "I offer hot stew and rumors." The engine did not reveal patrol_rumor on this turn.

Turn 2 selected npc:tavern_runner:patrol_rumor; public_fact_source=null. Authored topic carries discovery_categories=["rumor"]. Disclosure authorization rematches speaker, source, public classification, known status and permission=true. Authored proposition is the patrol disappearance/footprints rumor. No extra prerequisites or staged disclosure apply to this topic; deny-policy tests pass offline.

This conclusion uses actual selected authority and grant fields, not merely a response mentioning rumors. See knowledge_transition.json and T1/T2_internal_log.json.
