# mundane_actor

Objective: Test everyday physical affordances, safe movement, and action resolution without forcing success.

## Turn 1

Player: I look for a door, gate, stall, or posted route that seems usable.

GM: Nothing here matches that. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 2

Player: I try the most ordinary non-destructive way to use it.

GM: The simplest way to engage here yields no change—the notice board remains unchanged, its listings of taxes, curfew rules, and the missing patrol warning still intact. Around you, the rain persists, and the crowd stays restless under watchful eyes, yet no new path opens up immediately from this surface interaction.

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 3

Player: If it does not work, I ask the nearest person what I should do instead.

GM: You approach the nearest figure in the crowd—a gate guard standing watch beside the muddy queue. They’re the one managing patrols and responses.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 4

Player: Can they point me to someone who can help?

GM: Guard Captain says, "I do not know enough to answer that."

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 5

Player: I stop and ask for a clear yes, no, condition, or safer next step.

GM: I will not carry out that request; you will need another route.

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 6

Player: I take the next safe step they suggested.

GM: You step cautiously forward along the agreed path, the mud clutching at your boots beneath the chill drizzle. Nearby, the gate serjeant shifts his gaze from the roster board to watch the crowd, the tension between waiting travelers thick in the air. The ragged stranger eyes you briefly from the edge of the line, then turns back to the muddy road. The narrow lane ahead remains crowded, but your step follows the suggested safer route away from tighter scrutiny.

Semantic: `PASS`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 7

Player: What changes around me when I do that?

GM: The murmur around you never tightens into a single clear voice on that point.

Semantic: `FAIL`

Bounded: `{"entries": 0, "incidentals": 0, "npc_claims": 0, "rejected": 0, "latest": []}`

## Turn 8

Player: I ask whether there is a risk I should avoid.

GM: The murmur around you never tightens into a single clear voice on that point.

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
