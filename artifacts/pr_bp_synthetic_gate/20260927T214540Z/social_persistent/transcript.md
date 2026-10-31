# social_persistent

Objective: Talk naturally, follow up on claims, and persist once when answers are incomplete.

## Turn 1

Player: I greet the nearest approachable local and ask what people are worried about today.

GM: Guard Captain shakes their head. "I have heard talk, but I cannot verify it."

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 2

Player: What have you heard lately that a traveler should know?

GM: Guard Captain shakes their head.

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 3

Player: Who told you that?

GM: Guard Captain says, "I cannot verify the source or certainty of that earlier claim."

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 1, "latest": []}`

## Turn 4

Player: How certain are you, and who would know more?

GM: Guard Captain says, "I cannot verify the source or certainty of that earlier claim."

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 1, "latest": []}`

## Turn 5

Player: Can you introduce me or point me to them?

GM: Guard Captain says, "I will not carry out that request; you will need another route."

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 1, "latest": []}`

## Turn 6

Player: If you cannot help directly, what is one useful thing you can do?

GM: Guard Captain shakes their head.

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 1, "latest": []}`

## Turn 7

Player: I ask about food, lodging, or a safe place to wait.

GM: I cannot verify food, lodging, or a safe place to wait; you will need another source.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 1, "latest": []}`

## Turn 8

Player: What does that place look like from here?

GM: You look again. Nothing new resolves into evidence. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol.

Semantic: `FAIL`

Bounded: `{"entries": 1, "incidentals": 1, "npc_claims": 0, "rejected": 1, "latest": [{"id": "bi_9788a728593c", "kind": "incidental_fact", "category": "sensory_detail", "content": "From your vantage point amid the crowd at Cinderwatch Gate District, the scene is grim and bustling. Rain spatters down onto soot-dark stone beneath frayed banners hanging above the eastern gate. The muddy approach chokes with refugees, wagons, and travelers, all pressed between watchful guards holding the narrow gates. A weathered notice board stands nearby, its postings clearly visible: new taxes, curfew rules, and a stark warning about a missing patrol. The gate serjeant keeps a sharp eye on", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "dm_improvisation", "speaker_id": null, "epistemic_status": null, "status": "promoted", "authority": "bounded_improvisation", "truth_status": "runtime_incidental"}]}`

## Turn 9

Player: I press once, politely: who exactly can answer this, or what can you do for me right now?

GM: I cannot verify I press once, politely: who exactly can answer this, or what can you do for me r; you will need another source.

Semantic: `FAIL`

Bounded: `{"entries": 1, "incidentals": 1, "npc_claims": 0, "rejected": 1, "latest": [{"id": "bi_9788a728593c", "kind": "incidental_fact", "category": "sensory_detail", "content": "From your vantage point amid the crowd at Cinderwatch Gate District, the scene is grim and bustling. Rain spatters down onto soot-dark stone beneath frayed banners hanging above the eastern gate. The muddy approach chokes with refugees, wagons, and travelers, all pressed between watchful guards holding the narrow gates. A weathered notice board stands nearby, its postings clearly visible: new taxes, curfew rules, and a stark warning about a missing patrol. The gate serjeant keeps a sharp eye on", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "dm_improvisation", "speaker_id": null, "epistemic_status": null, "status": "promoted", "authority": "bounded_improvisation", "truth_status": "runtime_incidental"}]}`

## Turn 10

Player: I act on the most concrete lead they gave me.

GM: The guard says, "I do not know enough to answer that."

Semantic: `FAIL`

Bounded: `{"entries": 1, "incidentals": 1, "npc_claims": 0, "rejected": 1, "latest": [{"id": "bi_9788a728593c", "kind": "incidental_fact", "category": "sensory_detail", "content": "From your vantage point amid the crowd at Cinderwatch Gate District, the scene is grim and bustling. Rain spatters down onto soot-dark stone beneath frayed banners hanging above the eastern gate. The muddy approach chokes with refugees, wagons, and travelers, all pressed between watchful guards holding the narrow gates. A weathered notice board stands nearby, its postings clearly visible: new taxes, curfew rules, and a stark warning about a missing patrol. The gate serjeant keeps a sharp eye on", "scope": "scene", "scene_id": "frontier_gate", "consequence_level": "low", "source": "dm_improvisation", "speaker_id": null, "epistemic_status": null, "status": "promoted", "authority": "bounded_improvisation", "truth_status": "runtime_incidental"}]}`
