# C22 forensic traces (recorded before the repair)

Source session: `artifacts/pr_br_continuation21c/live/20261003T110414Z`.
Deterministic replay used the pre-repair engine. No model call.

## A. "listen carefully" owned the contract

Raw player input:

> I approach the tavern runner first, hoping to buy some hot stew and listen carefully to the whispered rumors he's offering, trying to learn more about the missing patrol and the overall mood among the crowd.

Replay:

- `_dimensions` → `('sound',)` because the sound pattern matches `listen`
- `_operation` → `perceive` (perception-dimension short-circuit)
- `terminal_resolution_operation` → `perceive` (`listen` matches; there is no `ask` token, so the ask-plus-perceive abstention does not run)
- contract operation `perceive`, dimension `sound`, interlocutor `tavern_runner`
- interpretation calls on the live turn: 0

The tavern runner was bound. The committed act is approaching that person to receive offered rumors and learn about the patrol. "listen carefully" is how the player attends to that speech. Nothing in clause structure, addressee, or purpose was consulted. The lexical sound cue won, and the safe fallback then spoke about the sound.

Cause: lexical dimension priority, not clause segmentation and not the structured interpreter.

## B. Conditional milestone movement

Raw player input (continuation 2, turn 3):

> I thank the tavern runner and turn toward the muddy lane northwest of the crates, carefully stepping through the rain to inspect the footprints they mentioned. I look for any signs or clues nearby that might hint at what happened to the missing patrol before deciding whether to follow the road toward the old milestone.

Replay:

- contract operation stayed `inspect`
- `slugify` of the full utterance contains `old_milestone`
- `resolve_place_phrase_to_exit_target` matches because `target_slug in dest_slug`
- `resolve_authored_exit_from_player_travel` returns `old_milestone`
- the same conditional clause alone also returns `old_milestone`
- the utterance with that clause removed returns no exit
- `parse_freeform_to_action` returns `scene_transition` to `old_milestone`, lane `authored_exit_resolution`

The referential head was `lane` and was not a person. The exit binder treats any mention of the destination id as current travel. `before deciding whether` is not a commitment.

Cause: authored-exit identity match on an uncommitted clause. Not incidental-person binding.

## C. Unresolved serjeant answered by the captain

Raw player input:

> I thank the tavern runner quietly, then turn toward the guard serjeant near the roster to ask about the missing patrol and the current state of affairs inside the gate. I observe the serjeant's demeanor carefully, looking for signs of stress or secrecy.

Live contract: operation `ask`, interlocutor id null, binding `ambiguous`, proposed `guard serjeant near roster to ask`. No incidental row. The runner was not restored. Accepted text is spoken by the guard captain. `speaker_conflict` was false. Hard validation passed.

Replay of the speaker check against the guard-captain catalog row (aliases include `guard`):

- `_catalog_ids("guard serjeant near roster to ask")` → `{guard_captain}`
- `_catalog_ids("guard captain")` → `{guard_captain}`
- the id intersection is non-empty, so `_speaker_conflicts` returns false
- the word sets also share `guard`, so the disjoint-word fallback would not fire either

`bound_interlocutor` is null, and the generic role alias `guard` is treated as identity with the captain. `serjeant` and `captain` are never compared.

Cause: unresolved explicit addressee is not a distinct speaker constraint. Shared generic role tokens authorize a different NPC.
