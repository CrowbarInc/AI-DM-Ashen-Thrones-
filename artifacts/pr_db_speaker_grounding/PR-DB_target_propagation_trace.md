# PR-DB Target Propagation Trace

Player input: "Does the rain make it harder to keep watch?"

1. Player input reaches `resolve_directed_social_entry` in `game.interaction_context`.
2. The session still has `active_interaction_target_id = guard_captain`, mode `social`, and the captain is addressable.
3. `_should_break_social_continuity_for_world_action` asks `_merged_text_has_self_directed_sustained_observation`.
4. Before this repair, the pattern `\bkee?p(?:s|ing)?\s+watch(?:ing)?\b` matched "keep watch" with no requirement that the player character be the watcher.
5. `apply_world_action_social_continuity_break` called `set_non_social_activity(session, "observe")`. That set `active_interaction_target_id` to null, `interaction_mode` to `activity`, and `engagement_level` to `focused`.
6. Discourse focus was not part of that clear. Resolution-contract construction still copied `guard_captain` from `discourse_focus.active_interlocutor`.
7. `resolve_authoritative_social_target` then ran. Continuity (section E) requires `session_allows_implicit_social_reply_authority`. That returns false when mode is `activity` or the kind is a non-social activity. The function returned `no addressable target resolved`.
8. Speaker selection consumed that social slice. `allowed_speaker_ids` stayed empty. `build_active_interlocutor_export` also returns null when the interaction target is empty, so the provider `active_interlocutor` was null.
9. `derive_interaction_obligation` reads `social.npc_id`, then the interaction target. Both were empty, so `interlocutor_id` was null. The question had no bound target, so `select_resolution_mode` returned `clarification_target_failure`.
10. The ordinary resolver was still `social` because the contract operation was `ask` with an interlocutor. That is why the contract and the speaker systems disagreed.
11. After the response, `_update_interaction_context_after_action` saw a social resolution kind and called `update_after_resolved_action`. That restores social mode and kind. It does not restore a target that was cleared earlier.

## Cause

The first boundary is the false self-observation clear, before social resolution.

Social grounding does not read `resolution_contract.interlocutor`. It reads the interaction target and explicit address cues. The contract can therefore name the Guard Captain while social and speaker selection see no target.

This is not a scene-id mismatch. It is not an explicit-target requirement blocking the follow-up. Finalization did not perform the original clear. It left the cleared target unset while putting the mode back to social.

Letter: F. The specific cause is the self-observation break. The downstream disagreement is that the recovered contract interlocutor is not an input to social or speaker selection.
