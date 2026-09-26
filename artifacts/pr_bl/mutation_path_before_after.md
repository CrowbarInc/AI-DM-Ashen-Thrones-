# Mutation Path Before / After

## Before

`I proceed northwest`
→ `parse_freeform_to_action` returns `None`
→ no travel owner
→ model narration can say the player reached a new road
→ `_validate_gm_scene_update_for_legacy_adoption` accepts the shape
→ overlay stores the arrival sentence, a new clue, a hidden fact, and `mode: exploration`
→ scene id does not change

## After

Directional `proceed` (`I proceed northwest`, `We proceed north`, `I proceed toward the bell loft`)
→ existing travel parse
→ exit resolver only when the destination phrase matches an authored exit
→ bare compass stays unresolved travel
→ narration agreement replaces a transition claim when `resolved_transition` is not success
→ the same rule runs if the parser still returns `None`
→ adoption drops the transition claim and the clues, hidden facts, and exploration/travel mode attached to it
→ a same-scene visible fact with no transition claim is still written

`activate_scene_id` and `new_scene_draft` stay advisory. Mentioned nouns are not promoted to interactables.
