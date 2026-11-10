# Narrative validation

PR-PLAY-75 accepted 0/6 live dialogue proposals because `validate_expression` required almost every content word to sit in the question or a tiny lexicon, and background conversation rejected a paraphrase unless relation words matched the host line exactly. PR-PLAY-77 accepted 1/4 provider plans.

This cycle did not turn those checks off. `bounded_social_line` is a separate operation:

- A–C (wording, ordinary detail, bounded character expression) may pass when they do not add a route, a secret, a reward, or a new identity.
- D (a new authoritative fact) fails the narration and speech checks used here. "Northwest" is rejected in narration validation. Withheld clue phrases are rejected in speech.
- E (a consequential change) is not granted by the provider. Success, movement, and discoveries stay on the host commit.

The bound is still loose for color that is not on the reject list. "Stay safe" and "keeping an eye on things" were accepted. "The mud track ahead gets tricky" was accepted before the guard was confined to the gate. That is the remaining validation gap: uncommitted but ordinary-sounding conditions can pass if they avoid the reject list.

Deterministic templates are the fallback. They are not counted as live content.
