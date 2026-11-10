# Reference and Target Grounding

Named targets match a token subset of the label or aliases. The highest token count wins. A tie asks which object is meant. Pronouns use `physical_focus`, otherwise the only object. Sit prefers objects whose use is `seat`, so "sit on it" can reach the only seat.

No match does not create an object, except the explicit loose-stone question described in the affordance report. Hidden interactables are skipped and their hidden notes are not published. An inaccessible seat is refused. Objects from another campaign or scene are not visible.
