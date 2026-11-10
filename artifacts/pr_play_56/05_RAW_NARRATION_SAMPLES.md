# Raw narration samples

The text below is the provider `output_text` stored as `raw_provider_text`. It was not rewritten before validation. The full response payloads are in `scenario_results.json` under `raw_provider_responses`.

## A1 — authorized discovery

The notice board stands weathered and crowded, its surface plastered with official decrees and urgent warnings. Nearby, the murmur of the gate serjeant and the clatter of the tavern runner’s footsteps mingle with the restless shifting of watchers and refugees. The board’s messages draw a steady stream of glances from those waiting in the muddy queue.

Engine anchor, appended after the prelude: "The missing patrol was last seen taking the northwest mud track past the crates."

## A2 — authorized discovery, second generation

The notice board stands weathered and worn, its surface crowded with official decrees and hastily scrawled warnings. Nearby, the murmur of the crowd blends with the occasional clatter of boots on mud, while a gate serjeant watches over the gathering with a wary eye.

Same engine anchor as A1.

## B1 — repeat search, nothing new

The notice board stands weathered and crowded, its wooden frame mottled by rain and age. Faded papers flutter weakly in the breeze, their ink smudged and difficult to decipher. Nearby, the murmur of the gate serjeant and the clatter of the tavern runner’s footsteps fill the damp air.

Engine anchors: "The examination adds nothing new to what you already know." Then the already-known route sentence.

## C1 — rain barrel, no clue

The rain barrel stands near the bustling gate, its surface slick with recent drizzle. The air carries the mingled scents of damp earth and simmering stew, while murmurs of the crowd ebb and flow around it. Shadows shift as watchers and travelers pass by, leaving the barrel’s purpose quietly unspoken.

Engine anchor begins: "No new clue is established by this examination." The public visible facts follow.

## C2 — rain barrel, second generation

The rain barrel stands near the bustling gate, its dark surface mottled by the steady drizzle. Steam rises faintly from the nearby stew, mingling with the damp air as murmurs and footsteps echo around the muddy line of watchers. The barrel’s quiet presence invites a closer look.

Same engine anchors as C1.

## D1 — footprint discovery

The ground near the weathered milestone is soft and disturbed, marked by a tangle of faint footprints that overlap and blur together. The muddied earth bears the subtle impressions of passage, but the details remain elusive beneath the shifting layers of soil and moisture.

Engine anchor: "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear."

## What the player actually saw

A and D player-facing lines are the deterministic inspection sentences plus the authorized clue. They do not contain the prelude.

B and C player-facing lines are: "Provider calls are disabled for this run, so no live narration was generated." That string is identical to the no-provider baseline. The prelude is not in it.

None of the six preludes contain a planted canary or a `frontier_gate` hidden fact.
