# Next step

Do not start the next milestone from this handoff.

## What this run still shows

The person-roster substitution on "tell me" and on an unmatched name is repaired. Negation and conditional admission still withhold. Explicit NPC binding, genuine "someone" clarification, and a present NPC's repeated warning still work.

Still failing on the ordinary path:

1. "I examine the book." does not see the carried spellbook. The reply asks which established object, and the turn advances. Object classification does not share the person roster. This was measured before and after; the text did not change.
2. "I look around." still becomes the provider-disabled narration and advances the turn. Three frozen broad rows still show that stub. Their text did not change in this replay.
3. Live-model grounding was not measured. Deterministic latency moved, and the quiet sample is in PERFORMANCE.md. That is not a provider-retry finding.

Reference continuity for the watcher follow-up and the patrol follow-up now stays on the same subject. The captain recall survives a reload. Broader continuity was not reopened.

## Recommendation

Next foundational milestone: the unique carried-object reference.

The book miss is the remaining grounding hole this investigation isolated. The player names one carried book. The surface classifier does not see inventory, reports no match, and still spends the turn. Person grounding cannot fix that owner. Narration that advances a turn on a provider stub is the following defect, and it was not changed by this repair.

Do not resume `pr_play_social_check_repeat_and_legacy_stance`. Do not open conversation, lore, combat, exploration, or equipment subsystems for the object miss. The next repair should stay on reference scope and turn withholding for that unresolved object.
