# PR-DB Implementation Report

MODE: CONVERSATIONAL SPEAKER GROUNDING

LIVE CALLS: 0

HEAD at start: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

The worktree was already dirty. It was not reset. Production saves were not used as the gameplay session.

PR-DA inherited decision: A — LIVE FOLLOW-UP VERIFIED

## What failed

The follow-up "Does the rain make it harder to keep watch?" already had an authoritative resolution-contract interlocutor, `guard_captain`. Social resolution, the interaction obligation, and speaker selection did not.

`speaker_selection.allowed_speaker_ids` was empty. `exactly_one_allowed_speaker` failed. Reduced context stayed off. That predicate was not weakened.

## First loss

`resolve_directed_social_entry` called `_should_break_social_continuity_for_world_action`. `_merged_text_has_self_directed_sustained_observation` treated the words "keep watch" inside the question as the player character taking up a watch.

`apply_world_action_social_continuity_break` then cleared `active_interaction_target_id` and set the interaction to `observe` / `activity`. Discourse focus was not cleared, so the resolution contract still named `guard_captain`. Social grounding and speaker selection read the interaction target, not the contract, so they reported `no addressable target resolved`.

After narration, social-kind finalization restored interaction mode to `social` and did not put the cleared target back. That is why the target was `guard_captain` before the turn and null after it.

## Repair

A question that only mentions a watch no longer counts as self-directed observation. A statement such as "He keeps watching the gate" still clears continuity. Player-performed watch questions ("I keep watch?") still clear it.

No new speaker selector was added. No speaker-validation bypass was added. Resolver selection was not changed. NPC availability rules were not changed.

## Result on the follow-up

- Resolver: `social`
- `resolution_contract.interlocutor`: `guard_captain`
- `interaction_obligation.interlocutor_id`: `guard_captain`
- `interaction_obligation.resolution_mode`: `grounded_information_request`
- `social.npc_id`: `guard_captain`
- `social.target_resolved`: true
- `speaker_selection.allowed_speaker_ids`: `[guard_captain]`
- `active_interaction_target_id` after the turn: `guard_captain`
- `discourse_focus.active_interlocutor`: `guard_captain`

## Reduced context

`exactly_one_allowed_speaker` now passes. Projection is not selected.

The next blocker, in source order, is `reply_plan_kind`. The social reply plan classifies this follow-up as `genuine_uncertainty`, and the projector requires `harmless_subjective_response_permitted`. `incidental_subjective_allowed` is false and `npc_speech_authority` is `none` for the same plan. Those predicates were not weakened.

## Decision

A — SPEAKER GROUNDING REPAIRED
