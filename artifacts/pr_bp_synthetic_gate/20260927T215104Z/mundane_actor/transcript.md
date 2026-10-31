# mundane_actor

Objective: Test everyday physical affordances, safe movement, and action resolution without forcing success.

## Turn 1

Player: I look for a door, gate, stall, or posted route that seems usable.

GM: Nothing here matches that. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 2

Player: I try the most ordinary non-destructive way to use it.

GM: The requested action cannot be completed here; another route is needed.

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 3

Player: If it does not work, I ask the nearest person what I should do instead.

GM: Guard Captain says, "I cannot verify what I should do instead; you will need another source."

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 4

Player: Can they point me to someone who can help?

GM: Guard Captain shakes their head. "I won't answer that about help—not here."

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 5

Player: I inspect the suggested place or object before touching it.

GM: Nothing here matches that. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 6

Player: I take the next safe step they suggested.

GM: You step forward with care, sweeping your gaze across the crowded gate district. The rain stiffens, dripping from mud-speckled cloaks and pooling beneath the camped refugees. The gate serjeant glances briefly your way but stays focused on the roster. Nearby, the tavern runner hollers another stew sale, undeterred by the weather or your movement. Ahead, the line inching toward the market gate seems your most guarded and sensible path. Each step is measured, avoiding slick patches or loose stones, while the chill air presses with quiet urgency.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 7

Player: What changes around me when I do that?

GM: As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster board.

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 8

Player: I ask whether there is a risk I should avoid.

GM: No reliable source here can verify the requested information; another source is needed.

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 9

Player: I choose a cautious route forward.

GM: Gate Serjeant mutters, "Word is, the patrol route changed after the Ash Compact census choke worsened."

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 10

Player: I confirm the immediate next action before I move on.

GM: The guard says, "I do not know enough to answer that."

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`
