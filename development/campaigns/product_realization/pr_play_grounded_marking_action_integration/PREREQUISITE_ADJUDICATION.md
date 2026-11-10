# Prerequisite Adjudication

A ready action requires all of the following, each with evidence the existing marking service already demands:

- The target instance exists, is accessible, and the possessor may mark it.
- The surface is an authored ordinary-writing surface.
- The medium exists, is accessible, and is compatible with that surface.
- The content is one established disclosed source or a literal supplied in the utterance.
- The character is not marked unable. `physical_status.ordinary_marking == "unable"` or a condition with `blocks_ordinary_marking: true` blocks the action.

Destructive operations stop before resource resolution and do not invent a surface or a medium.

The universal path does not embed a PF1e skill name, difficulty class, spell, or technology rule. When a surface or medium says `mechanics: required`, the action stays unresolved and says a rules decision is needed. No roll is invented.

When `consumption: required`, the action is not completed. A singleton quantity cannot be decremented without breaking identity, and no consumption rule was invented. Quantity stays unchanged and narration does not claim the medium was used up.
