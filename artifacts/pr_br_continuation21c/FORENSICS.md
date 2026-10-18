# Continuation 2 fresh failure, and the Turn 3 move

Source session: `artifacts/pr_br_continuation21b/live/20261002T111028Z`. Interpretation calls on the failing turn: 0. No repair and no rerun were performed in that session.

## Turn 3 referential failure

Raw player input:

> I thank the tavern runner and turn toward the muddy lane northwest of the crates, carefully stepping through the rain to inspect the footprints they mentioned. I look for any signs or clues nearby that might hint at what happened to the missing patrol before deciding whether to follow the road toward the old milestone.

Extracted candidate span: `the muddy lane northwest of the crates`.

Candidate before the head check: `the muddy lane northwest of the crates`.

Modifier stripping then: the `of the crates` complement was removed because the left side still had content words. The purpose infinitive, participle, and locative-preposition strippers did not match `northwest`. What remained was `the muddy lane northwest`.

Token selected as semantic head: `northwest`.

Why: `_raw_head` took the last remaining content word. `northwest` was not in the non-person set, so personhood returned true.

Personhood classification: person.

Incidental entity: `inc_d06766ba95`, label `muddy lane northwest`, reasons `scene:populated` and `pr_bn:accepted`.

Persistence: stored on the incidental ledger. Discourse interlocutor became that id on `old_milestone`. It did not speak.

Player-visible consequence of the bad binding: the stored interlocutor was a route. The visible placement beside the milestone is a separate action, traced below.

## Turn 3 movement

The same utterance was also classified by the world-action parser.

With the referential-head repair applied, a deterministic replay of the original sentence gives:

- resolution-contract operation: `inspect`
- proposed span: `the muddy lane northwest of the crates`
- referential head: `lane`
- personhood: `unknown` (abstain)
- binding: `unresolved`, reason `proposal:personhood_unresolved`
- no incidental entity
- previous tavern runner not restored
- world action: `scene_transition` to `old_milestone`, parser lane `authored_exit_resolution`

The same sentence with the final conditional clause removed:

> I thank the tavern runner and turn toward the muddy lane northwest of the crates, carefully stepping through the rain to inspect the footprints they mentioned.

resolves as `investigate` of the footprints. `resolve_authored_exit_from_player_travel` returns no exit.

The conditional clause alone:

> before deciding whether to follow the road toward the old milestone.

resolves to `old_milestone`.

`extract_travel_destination_phrase` on the full sentence is `None`. The exit binder still matches the utterance to the authored frontier-gate exit whose destination is `old_milestone` (`Follow the missing patrol rumor`). `whether` is not treated as an uncommitted intention.

## Causality

The malformed person did not select `old_milestone`. After the head repair, the lane is not a person and the exit transition still fires. The two defects coincided on one turn.

The movement is a separate deterministic mechanism: a stated future conditional (`before deciding whether to follow`) is executed as current travel. It is not coupled to referential-head extraction. This continuation does not change that parser.
