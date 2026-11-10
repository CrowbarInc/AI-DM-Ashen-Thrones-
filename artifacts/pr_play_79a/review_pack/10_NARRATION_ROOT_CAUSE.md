# Narration root cause

`validate_narration` used to reject the word "northwest" and the phrase "hidden passage" even when the committed facts or a discovered clue already contained them, and even when the phrase was negated. The deterministic fallback could still say "northwest mud track."

The validator now allows a direction that appears in the committed facts or in a discovered/known clue, and it allows a banned phrase that is already in that text or negated in the preceding words. An exact copy is still not a variation. "You discover", "you find", "you climb", attack, blood, dragged, gold, and hidden camp remain rejected when they are not already established.
