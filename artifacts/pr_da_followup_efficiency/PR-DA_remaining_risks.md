# PR-DA Remaining Risks

- Reduced context stayed off. The first failing predicate is `exactly_one_allowed_speaker`: `speaker_selection.allowed_speaker_ids` is empty because speaker grounding reported `no addressable target resolved`.
- The ask contract still names `guard_captain`, and the answer spoke as the Guard Captain. The provider payload's `active_interlocutor` remained null, and `interaction_obligation.interlocutor_id` remained null.
- After the accepted turn, `discourse_focus.active_interlocutor` is still `guard_captain`, while `interaction_context.active_interaction_target_id` changed from `guard_captain` to null.
- Hypothetical reduced-context size is not a live saving.
- One accepted follow-up does not show that every ordinary continuation will validate on the first attempt.
- The shared turn-pipeline suite was not rerun.
- Production saves were left untouched. The gameplay session was an isolated copy of the PR-CY Turn 1 state.
