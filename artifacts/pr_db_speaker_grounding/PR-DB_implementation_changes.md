# PR-DB Implementation Changes

## `game/interaction_context.py`

`_merged_text_has_self_directed_sustained_observation` still uses the existing watch patterns. If the line is a question and `_PLAYER_PERFORMED_WATCH_RE` does not show the player character performing the watch, the function returns false.

That keeps ordinary follow-ups on the existing social continuity path:

`resolve_directed_social_entry` -> dialogue-first question action -> `resolve_social_action` -> `build_speaker_selection_contract`

The dialogue-first action copies `target_actor_id` from the directed-entry result. For this follow-up that id is `guard_captain` with reason `active_interlocutor_followup`. Speaker selection then reports the existing explicit-target reason `normalized target_id matches scene-addressable roster`.

No second selector was added. `exactly_one_allowed_speaker` was not edited. `_project_harmless_social_provider_context` was not edited. The harmless-subjective reply-plan regex was not edited.

## `tests/test_pr_db_speaker_grounding.py`

Deterministic replay of the three-turn exchange and the negative controls. No provider calls.

## Measurement helper

`artifacts/pr_db_speaker_grounding/_measure.py` rebuilds the follow-up provider payload locally. It does not call a model.
