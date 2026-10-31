# social_persistent

Objective: Talk naturally, follow up on claims, and persist once when answers are incomplete.

## Turn 1

Player: I greet the nearest approachable local and ask what people are worried about today.

GM: Guard Captain shakes their head. "I have heard talk, but I cannot verify it."

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 2

Player: What have you heard lately that a traveler should know?

GM: Guard Captain says, "I couldn't tell you What have you heard lately that a traveler should know; you will need another source."

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 3

Player: Who told you that?

GM: Guard Captain says, "I cannot verify the source or certainty of that earlier claim."

Semantic: `PASS`

Bounded: `{"entries": 1, "incidentals": 0, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c62cd758bc22", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain says carefully, their gaze steady but refusing to elaborate. \"If you want reliable news, you might find better answers from the tavern runner or some of the watchers gathered nearby.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}]}`

## Turn 4

Player: How certain are you, and who would know more?

GM: Guard Captain says, "I cannot verify the source or certainty of that earlier claim."

Semantic: `FAIL`

Bounded: `{"entries": 1, "incidentals": 0, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c62cd758bc22", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain says carefully, their gaze steady but refusing to elaborate. \"If you want reliable news, you might find better answers from the tavern runner or some of the watchers gathered nearby.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}]}`

## Turn 5

Player: Can you introduce me or point me to them?

GM: Guard Captain says, "I will not carry out that request; you will need another route."

Semantic: `FAIL`

Bounded: `{"entries": 1, "incidentals": 0, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c62cd758bc22", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain says carefully, their gaze steady but refusing to elaborate. \"If you want reliable news, you might find better answers from the tavern runner or some of the watchers gathered nearby.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}]}`

## Turn 6

Player: If you cannot help directly, what is one useful thing you can do?

GM: Guard Captain shakes their head. "I have heard talk, but I cannot verify it."

Semantic: `PASS`

Bounded: `{"entries": 1, "incidentals": 0, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c62cd758bc22", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain says carefully, their gaze steady but refusing to elaborate. \"If you want reliable news, you might find better answers from the tavern runner or some of the watchers gathered nearby.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}]}`

## Turn 7

Player: I ask about food, lodging, or a safe place to wait.

GM: If you're looking for a safer spot or a warm meal, the tavern runner near the rain barrel knows the best places to go, though you'll need to keep your wits about you.

Semantic: `FAIL`

Bounded: `{"entries": 1, "incidentals": 0, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c62cd758bc22", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain says carefully, their gaze steady but refusing to elaborate. \"If you want reliable news, you might find better answers from the tavern runner or some of the watchers gathered nearby.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}]}`

## Turn 8

Player: What does that place look like from here?

GM: From your vantage near the Cinderwatch Gate District, rain falls steadily, streaking the soot-darkened stones and fraying the banners hanging overhead. The eastern gate itself is choked with a restless crowd: refugees, laden wagons, and a knot of travelers pressing against the guarded chokepoint. A notice board near the gate wears the marks of recent disruptions—its postings advertise new taxes, strict curfews, and a stark warning about a missing patrol. The gate serjeant stands watch, eyes dart

Semantic: `FAIL`

Bounded: `{"entries": 2, "incidentals": 1, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c62cd758bc22", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain says carefully, their gaze steady but refusing to elaborate. \"If you want reliable news, you might find better answers from the tavern runner or some of the watchers gathered nearby.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}, {"id": "bi_3b117439fc05", "kind": "incidental_fact", "category": "sensory_detail", "content": "From your vantage near the Cinderwatch Gate District, rain falls steadily, streaking the soot-darkened stones and fraying the banners hanging overhead. The eastern gate itself is choked with a restless crowd: refugees, laden wagons, and a knot of travelers pressing against the guarded chokepoint. A notice board near the gate wears the marks of recent disruptions—its postings advertise new taxes, strict curfews, and a stark warning about a missing patrol. The gate serjeant stands watch, eyes dart", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "dm_improvisation", "speaker_id": null, "epistemic_status": null, "status": "promoted", "authority": "bounded_improvisation", "truth_status": "runtime_incidental"}]}`

## Turn 9

Player: I thank them and ask for one final warning before I move.

GM: If you value your freedom, keep to the rules and avoid drawing undue attention. Nearby, the gate serjeant shifts restlessly, his eyes scanning the restless crowd.

Semantic: `FAIL`

Bounded: `{"entries": 2, "incidentals": 1, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c62cd758bc22", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain says carefully, their gaze steady but refusing to elaborate. \"If you want reliable news, you might find better answers from the tavern runner or some of the watchers gathered nearby.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}, {"id": "bi_3b117439fc05", "kind": "incidental_fact", "category": "sensory_detail", "content": "From your vantage near the Cinderwatch Gate District, rain falls steadily, streaking the soot-darkened stones and fraying the banners hanging overhead. The eastern gate itself is choked with a restless crowd: refugees, laden wagons, and a knot of travelers pressing against the guarded chokepoint. A notice board near the gate wears the marks of recent disruptions—its postings advertise new taxes, strict curfews, and a stark warning about a missing patrol. The gate serjeant stands watch, eyes dart", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "dm_improvisation", "speaker_id": null, "epistemic_status": null, "status": "promoted", "authority": "bounded_improvisation", "truth_status": "runtime_incidental"}]}`

## Turn 10

Player: I act on the most concrete lead they gave me.

GM: You approach the notice board again, eyes catching the posted warning about the missing patrol more closely. The list mentions that the patrol was last seen taking the northwest mud track past the crates on the outskirts. This faint lead points you toward the edge of the district where the landscape narrows into muddy trails flanked by scuffed wooden crates. Though the crowd and gate guards allow you no direct escort or detailed guidance, you now know where the missing patrol was headed and a suitable path to investigate yourself.

Semantic: `PASS`

Bounded: `{"entries": 2, "incidentals": 1, "npc_claims": 1, "rejected": 0, "latest": [{"id": "bi_c62cd758bc22", "kind": "npc_claim", "category": "rumor", "content": "\"I don't have a specific source to name,\" the guard captain says carefully, their gaze steady but refusing to elaborate. \"If you want reliable news, you might find better answers from the tavern runner or some of the watchers gathered nearby.\"", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "npc:guard_captain", "speaker_id": "guard_captain", "epistemic_status": "hearsay", "status": "promoted", "authority": "bounded_improvisation", "truth_status": "not_world_truth"}, {"id": "bi_3b117439fc05", "kind": "incidental_fact", "category": "sensory_detail", "content": "From your vantage near the Cinderwatch Gate District, rain falls steadily, streaking the soot-darkened stones and fraying the banners hanging overhead. The eastern gate itself is choked with a restless crowd: refugees, laden wagons, and a knot of travelers pressing against the guarded chokepoint. A notice board near the gate wears the marks of recent disruptions—its postings advertise new taxes, strict curfews, and a stark warning about a missing patrol. The gate serjeant stands watch, eyes dart", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "dm_improvisation", "speaker_id": null, "epistemic_status": null, "status": "promoted", "authority": "bounded_improvisation", "truth_status": "runtime_incidental"}]}`
