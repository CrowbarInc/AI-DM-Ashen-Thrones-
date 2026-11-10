# Local movement and contact contract

Owner: `resolve_transient_local_action` in `game/local_interaction.py`, reached from the existing local-presence decision and, for contact that is not a move clause, from `deterministic_conversational_decision` after committed movement returns none.

## Eligible actions

One first-person approach, one simple contact, or both as two clauses joined by “and”:

- Approach verbs: walk over to, step up to, go over to, approach.
- Contact: put, place, rest, or lay a hand on or against; or touch.
- A contact part may be frame, surface, edge, rail, railing, post, rim, or side of the approached object.

The target must be unique. Names come from the object label, name, and aliases. No object name is hard-coded.

## Eligibility

All of the following are required:

1. The target is in the current scene’s visible catalog as `inspect_target` or `perceive_target`.
2. The phrase matches exactly one such object.
3. The action is not a scene transition. Exit and travel matches stay with the travel owner because this resolver returns none for consequential and information verbs, and committed travel still runs first.
4. Positive accessibility: `classify_referenced_surface` reports `authored_interactable` for that same id, with existence, visibility, and inspectability. Absence of a blocking flag is not enough.
5. No unresolved `skill_check` with a `skill_id`.
6. The utterance does not ask to take, open, close, unlock, break, damage, write, copy, read, examine, inspect, ask, speak, push, pull, lift, or otherwise mutate.
7. No veto: hidden, `visible` false, `accessible` false, `reachable` false, availability other than available, or locked/barred/blocked/inaccessible/unreachable/impassable in the row text. Combat mode and an in-combat session are refused by returning none.

## Transient outcome

A completed record identifies `target_id`, `label`, `action_category`, `categories`, per-part `completion` (`completed` or `not_requested`), `authority_basis`, `scene_transition: false`, `persistent_state_changed: false`, `narration_authorized: true`, `player_facing_text`, and `scene_id`. Status is `completed`. Reason is `transient_local_action_completed`.

The record is not a database write. Scene id, inventory, and world truth stay as they were. Narration may describe the completed approach and/or contact only because this record authorizes it.

Refusals use the same record shape with `status: refused` and `narration_authorized: false`:

- Ambiguous visible matches ask which object and state that nothing was attempted.
- Hidden matches say nothing here matches that, and do not name the hidden object.
- Inaccessible matches name the visible object and say it was not approached or touched.
- An unresolved skill check says nothing was attempted.

## Compound limit

At most two clauses. Each clause is only an approach or only a contact. A second approach, a second contact, or three or more clauses returns none so the existing owners remain responsible. If only one part is authorized, the narration describes only that part.

## Excluded consequential actions

Take, open, damage, write, copy, read, inspect, and speech return none. They are not rewritten into a successful touch. T06’s request to copy the patrol warning onto a sleeve stays the existing unsupported-manipulation refusal.

## Authority precedence

- Genuine travel still uses the travel admission and move resolver.
- NPC-only matches return none so dialogue is not converted into fixture contact.
- Reading a notice stays on the inspection and clue path.
- When `ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION` is enabled, this resolver returns none and does not override that owner. The pre-existing local-presence decline still short-circuits before that owner sees the turn; this cycle does not change that gate.
- An owner that already returned a committed movement decision is not replaced.
