# mundane_actor

Objective: Test everyday physical affordances, safe movement, and action resolution without forcing success.

## Turn 1

Player: I look for a door, gate, stall, or posted route that seems usable.

GM: Nothing here matches that. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 2

Player: I try the most ordinary non-destructive way to use it.

GM: I will not carry out that request; you will need another route.

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 3

Player: If it does not work, I ask the nearest person what I should do instead.

GM: Guard Captain shakes their head. "I have heard talk, but I cannot verify it."

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 4

Player: Can they point me to someone who can help?

GM: Guard Captain shakes their head.

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 5

Player: I inspect the suggested place or object before touching it.

GM: Nothing here matches that. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 6

Player: I take the next safe step they suggested.

GM: You step cautiously, navigating the crowded muddy queue with care. The gate serjeant’s watchful eyes track your movement as you move a little closer to the gate, but the pressing crowd swallows you again, a sea of faces marked by exhaustion and guarded hope.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 7

Player: What changes around me when I do that?

GM: The guard says, "I do not know enough to answer that."

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 8

Player: I stop and ask for a clear yes, no, condition, or safer next step.

GM: I cannot verify the requested information from what I know; you will need another source.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 9

Player: I choose a cautious route forward.

GM: Gate Serjeant mutters, "Word is, the patrol route changed after the Ash Compact census choke worsened."

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 10

Player: I confirm the immediate next action before I move on.

GM: You pause, relying on the guarded atmosphere around the gate. No official summons or clear guidance emerges from the serjeant or the guard captain, who only exchange wary looks while managing the crowd and glancing toward the muddy northwest track—the last known route of the missing patrol. Beyond these subtle signs, no firm immediate next action is confirmed for you. The option to investigate the muddy track, press deeper into the wary clusters of refugees and watchers, or enter Cinderwatch remains open for now.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`
