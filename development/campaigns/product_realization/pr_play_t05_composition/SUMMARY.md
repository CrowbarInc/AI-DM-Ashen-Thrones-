# T05 Authorized Clue Publication Composition Repair

Milestone `pr_play_t05_composition`, client date 2026-11-08. **A/PASS for the bounded repair. The game remains incomplete.** The predecessor `pr_play_preseal_authority` assigned a descriptive next action, not a numbered milestone. This identifier implements that action; PR-PLAY-80 and AT-OPT-07 remain unopened.

Root cause: `game/response_policy_enforcement.py::enforce_scene_momentum` appends synthetic pressure from `render_scene_momentum_diegetic_append` to a resolver-selected clue. The existing compatibility guard verifies that the answer survives, not that the stock addition belongs to the requested disclosure. This is an implementation composition defect; hard validation and immutable publication faithfully retain the already contaminated candidate.

Only production change: decline that renderer's append when `revealed_information(resolution)` selects newly authorized information. Existing candidate prose and resolved events remain intact; no sentence splitting, relevance classifier, exact-string suppression, provider pass, prompt change or authority-projection edit.

Original T05: The missing patrol was last seen taking the northwest mud track past the crates. Someone jabs at the board in Cinderwatch Gate District, impatient with anyone who reads too long.

Corrected T05: You inspect notice board. The missing patrol was last seen taking the northwest mud track past the crates.

The original twelve-turn HTTP path confirms the clue, normal hard validation, immutable digest and accepted/published/pointer identity. Inventory and location stay unchanged; authorized clue knowledge still advances. The other eleven publications, all intent kinds, routes, disclosures, resolution state changes, scenes and refusal outcomes remain equivalent. Pointer text changes on T05 and on T06 while it retains the last successful publication; subsequent pointer behavior is preserved.

Fresh same-source baseline: **378 passed / 20 failed** before and after, matching the predecessor. Added tests: **7 passed / 8 failed before → 15 passed / 0 failed after**. Combined after: **393 passed / 20 failed**, zero collection errors/skips. No new failure identities or changed normalized baseline diagnostics. Three original closed inspections and all 17 pre-seal controls pass; seven conversational HTTP controls and AT-OPT-06 controls remain green.

Remaining limitations: T01/T07 disabled narration; T02 unhelpful NPC answer; T04/T06 incomplete physical actions; T08 generic acknowledgment; T10 improvised trading; T12 operational refusal. Twenty baseline failures remain: twelve obsolete public-resolution assertions, one stew mismatch, four authority/refusal/publication failures including the portal exception, and three unrelated KeyErrors. No full suite, independent held-out generalization, live-provider or Gameplay Benchmark claim.

Live provider calls: **0**. No commits or pushes. Archive verification and hash: artifacts/pr_play_t05_composition/archive_verification.json and archive_sha256.txt.
