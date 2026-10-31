# social_persistent

Objective: Talk naturally, follow up on claims, and persist once when answers are incomplete.

## Turn 1

Player: I greet the nearest approachable local and ask what people are worried about today.

GM: Guard Captain shakes their head. "I have heard talk, but I cannot verify it."

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 2

Player: What have you heard lately that a traveler should know?

GM: Guard Captain says, "I cannot verify What have you heard lately that a traveler should know; you will need another source."

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 3

Player: Who told you that?

GM: Guard Captain says, "I cannot verify the source or certainty of that earlier claim."

Semantic: `PASS`

Bounded: `{"entries": 1, "incidentals": 0, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c003dd39e04d", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain replies evenly, their gaze steady and unwavering. \"What I have are reports and rumors that circulate among the watch and the town, but nothing I can confirm for certain. If you seek something reliable, you might find better answers with the tavern runner or by checking the notice board again.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}]}`

## Turn 4

Player: How certain are you, and who would know more?

GM: Guard Captain says, "I cannot verify the source or certainty of that earlier claim."

Semantic: `FAIL`

Bounded: `{"entries": 1, "incidentals": 0, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c003dd39e04d", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain replies evenly, their gaze steady and unwavering. \"What I have are reports and rumors that circulate among the watch and the town, but nothing I can confirm for certain. If you seek something reliable, you might find better answers with the tavern runner or by checking the notice board again.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}]}`

## Turn 5

Player: Can you introduce me or point me to them?

GM: Guard Captain says, "I will not carry out that request; you will need another route."

Semantic: `FAIL`

Bounded: `{"entries": 1, "incidentals": 0, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c003dd39e04d", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain replies evenly, their gaze steady and unwavering. \"What I have are reports and rumors that circulate among the watch and the town, but nothing I can confirm for certain. If you seek something reliable, you might find better answers with the tavern runner or by checking the notice board again.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}]}`

## Turn 6

Player: If you cannot help directly, what is one useful thing you can do?

GM: Guard Captain says, "I cannot verify If you cannot help directly, what is one useful thing you can do; you will need another source."

Semantic: `PASS`

Bounded: `{"entries": 1, "incidentals": 0, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c003dd39e04d", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain replies evenly, their gaze steady and unwavering. \"What I have are reports and rumors that circulate among the watch and the town, but nothing I can confirm for certain. If you seek something reliable, you might find better answers with the tavern runner or by checking the notice board again.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}]}`

## Turn 7

Player: I ask about food, lodging, or a safe place to wait.

GM: No reliable source here can verify food, lodging, or a safe place to wait; another source is needed.

Semantic: `PASS`

Bounded: `{"entries": 1, "incidentals": 0, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c003dd39e04d", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain replies evenly, their gaze steady and unwavering. \"What I have are reports and rumors that circulate among the watch and the town, but nothing I can confirm for certain. If you seek something reliable, you might find better answers with the tavern runner or by checking the notice board again.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}]}`

## Turn 8

Player: What does that place look like from here?

GM: From this vantage at the Cinderwatch Gate District, the scene is muted and tense beneath the steady drizzle. Rain pelts the soot-darkened stone and frayed banners flutter listlessly overhead. The narrow approach throbs with muddied, congested traffic—refugees, wagons, and foot travelers jostle while guards hold firm at the chokepoints. Near the worn notice board, listings include new taxes, curfew rules, and a conspicuous warning about a missing patrol. A gate serjeant keeps watch over the crowd

Semantic: `PASS`

Bounded: `{"entries": 2, "incidentals": 1, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c003dd39e04d", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain replies evenly, their gaze steady and unwavering. \"What I have are reports and rumors that circulate among the watch and the town, but nothing I can confirm for certain. If you seek something reliable, you might find better answers with the tavern runner or by checking the notice board again.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}, {"id": "bi_dd8f10fd2427", "kind": "incidental_fact", "category": "sensory_detail", "content": "From this vantage at the Cinderwatch Gate District, the scene is muted and tense beneath the steady drizzle. Rain pelts the soot-darkened stone and frayed banners flutter listlessly overhead. The narrow approach throbs with muddied, congested traffic—refugees, wagons, and foot travelers jostle while guards hold firm at the chokepoints. Near the worn notice board, listings include new taxes, curfew rules, and a conspicuous warning about a missing patrol. A gate serjeant keeps watch over the crowd", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "dm_improvisation", "speaker_id": null, "epistemic_status": null, "status": "promoted", "authority": "bounded_improvisation", "truth_status": "runtime_incidental"}]}`

## Turn 9

Player: I thank them and ask for one final warning before I move.

GM: No reliable source here can verify the requested information; another source is needed.

Semantic: `FAIL`

Bounded: `{"entries": 2, "incidentals": 1, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c003dd39e04d", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain replies evenly, their gaze steady and unwavering. \"What I have are reports and rumors that circulate among the watch and the town, but nothing I can confirm for certain. If you seek something reliable, you might find better answers with the tavern runner or by checking the notice board again.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}, {"id": "bi_dd8f10fd2427", "kind": "incidental_fact", "category": "sensory_detail", "content": "From this vantage at the Cinderwatch Gate District, the scene is muted and tense beneath the steady drizzle. Rain pelts the soot-darkened stone and frayed banners flutter listlessly overhead. The narrow approach throbs with muddied, congested traffic—refugees, wagons, and foot travelers jostle while guards hold firm at the chokepoints. Near the worn notice board, listings include new taxes, curfew rules, and a conspicuous warning about a missing patrol. A gate serjeant keeps watch over the crowd", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "dm_improvisation", "speaker_id": null, "epistemic_status": null, "status": "promoted", "authority": "bounded_improvisation", "truth_status": "runtime_incidental"}]}`

## Turn 10

Player: I act on the most concrete lead they gave me.

GM: The requested action cannot be completed here; another route is needed.

Semantic: `FAIL`

Bounded: `{"entries": 2, "incidentals": 1, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c003dd39e04d", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain replies evenly, their gaze steady and unwavering. \"What I have are reports and rumors that circulate among the watch and the town, but nothing I can confirm for certain. If you seek something reliable, you might find better answers with the tavern runner or by checking the notice board again.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}, {"id": "bi_dd8f10fd2427", "kind": "incidental_fact", "category": "sensory_detail", "content": "From this vantage at the Cinderwatch Gate District, the scene is muted and tense beneath the steady drizzle. Rain pelts the soot-darkened stone and frayed banners flutter listlessly overhead. The narrow approach throbs with muddied, congested traffic—refugees, wagons, and foot travelers jostle while guards hold firm at the chokepoints. Near the worn notice board, listings include new taxes, curfew rules, and a conspicuous warning about a missing patrol. A gate serjeant keeps watch over the crowd", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "dm_improvisation", "speaker_id": null, "epistemic_status": null, "status": "promoted", "authority": "bounded_improvisation", "truth_status": "runtime_incidental"}]}`
