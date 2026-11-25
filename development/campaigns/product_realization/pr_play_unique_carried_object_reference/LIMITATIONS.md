# Limitations

`classify_referenced_surface` still does not receive the character. A direct call on "I examine the book." at the frontier gate remains `unsupported`. The ordinary chat owner resolves the carried spellbook before that result can be published.

A compound head must be one token of at least four letters at the end of a longer name token. `book` matches `spellbook`. A shorter stem such as `bow` does not match `crossbow`. A head can still match an unintended longer word when that word is the unique eligible object, for example `stone` at the end of `milestone` if the player says only "the stone" and a milestone is the unique visible object. The scene's authored alias `stone` already did that for the old milestone.

Objects outside the current scene and the current character sheet are not targets. Examining the weathered milestone from the hidden meeting room stays unmatched.

Inventory examination does not become a supported read, search, or equip. The sheet can acknowledge identity and refuse unestablished details. Equip still follows its existing path and still does not equip.

"I look around." still publishes "Provider calls are disabled for this run, so no live narration was generated." and still advances the turn. Three frozen broad rows still show that stub.

A hidden fact that shares one token, such as `silver`, is still labeled `authored_hidden` by the surface classifier. The public examine path does not use that fact as the object and does not spend the turn.

Live-model object-grounding reliability: NOT MEASURED.

No commit and no push. `pr_play_social_check_repeat_and_legacy_stance` was not resumed.
