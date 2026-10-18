# 05 — Ambiguous-Target Integrity

## Historical failure

“I ask one of them what happened.” The lexical binder left the addressee unresolved. The provider supplied `sergeant_mara`. The contract copied that id, the social resolver treated it as explicit, and the turn advanced time and faction pressure.

## After

Scripted provider id `sergeant_mara`, two visible NPCs, same sentence: no social result, no turn, clock, faction, or world change. The line names the visible people and says nothing has been attempted. The provider id is a candidate on the authorization record (`provider_target`), with `conflict_status=unresolved`.

The same sentence with the provider saying GM and supplying no target also clarifies and does not tick.

One visible NPC and “I put the question to one of them.” clarifies. A single convenient NPC is not enough.

“I ask either guard about the patrol.” and “I ask someone nearby…” clarify.

“I ask the taller guard about the gate.” executes Corporal Bren only when his description or a sentence that names him says he is taller. Without that fact, two guards stay ambiguous. The engine does not invent the distinction.

“I ask him…” with one visible person executes that person.

## Fresh live

Turn 5, both guards present, fresh interpretation: “Which person do you mean: Sergeant Mara or Corporal Bren? Nothing has been attempted.” Turn counter stayed 2. Clocks and factions did not change. The authorization record says `requires_clarification`, `ambiguous`, `mutation_eligibility=false`, provenance `communication_decision`.

Turn 6, after an explicit save/load of that pending record: “The sergeant.” resolved to `sergeant_mara`, kind `question`, turn 2 → 3. The clarified request was allowed to execute under the existing social and timing rules.

## One-NPC live wording

The frozen live holdout “I put the question to one of them.” clarified and did not mutate (`state_pass`). The spoken line was the provider’s “Which NPC is the character addressing with the question?” rather than “Do you mean Sergeant Mara?”. No consequential operation ran.
