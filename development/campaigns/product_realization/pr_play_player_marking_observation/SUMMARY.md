# Summary

Milestone: `pr_play_player_marking_observation`. Date: 2026-11-09.

**Verdict: A/PASS.**

A player can examine the current visible markings on an established carried object through the existing chat turn. The turn recognizes the request, resolves one accessible surface, builds an ordinary observation grant from inventory state, and publishes only what `game.object_observation.observe_object` returns. Concealed, restricted, legacy, and removed markings stay out of that sentence. Observation does not write the character. The same sentence is recovered after save/reload and from the matching snapshot.

Publication integrity: if narration sealing returns text that denies the committed marking, omits its content, or contradicts its visibility, that text is not published. The character remains committed, and the player receives the deterministic committed-outcome sentence. A compatible paraphrase may be published. A sealer exception or a failed session write is a publication failure, not a second mutation.

Original T06 stays the grounded unresolved marking sentence. T04, T05, T09, T11, and T12 match the immediate predecessor. Live provider calls: **0**.

Exactly one next milestone: `pr_play_grounded_marking_removal`. Do not begin it automatically.
