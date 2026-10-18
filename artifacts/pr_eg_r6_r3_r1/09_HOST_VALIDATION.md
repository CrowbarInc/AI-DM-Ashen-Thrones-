# 09 — Host Validation

The host rejects unknown, forged, and cross-turn ids. A referent must belong to the current conversation and must not be a corrected record. Replacement values are kept only when the value occurs in the player utterance; a paraphrased evidence quote is narrowed to that value, and a value that does not occur is rejected. Unlisted roles are copied. Empty reversals that also fill new values are rejected (`reverse_must_be_empty`). Failed selections do not commit referents.
