# PR-DB Remaining Risks

Reduced context still does not activate for "Does the rain make it harder to keep watch?" The speaker is now `guard_captain`, and the projector stops on `social.reply_plan_kind = genuine_uncertainty`. Widening that classifier would change what counts as harmless subjective speech. It was left unchanged.

An open call such as "Can anyone..." is not treated as a private follow-up. The existing dialogue-first path can still bind one in-scene NPC. That acquisition was already there.

"I attack the guard captain" clears the interaction target and leaves activity mode, but speaker selection can still list `guard_captain` because the attack's normalized target matches that NPC. That is the existing explicit-target rule.

If discourse focus and the interaction target start on different NPCs, this follow-up grounds the interaction target and the discourse commit then stores that same id. It does not keep both.

Shared-pipeline failures remain: 24 failed. Authored-knowledge realization still fails 3 tests. Neither set was repaired.

The after-repair byte count is a fresh harness payload. It is not a live token saving and it is not a subtraction from the PR-DA 127,336-byte capture. No tokenizer is vendored here, so exact token counts were not computed.

The inherited dirty worktree was preserved. Unrelated modifications were not reverted.
