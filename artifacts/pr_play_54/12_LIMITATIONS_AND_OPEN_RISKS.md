# Limitations and open risks

The checker is a deterministic frame comparison. It is not a proof that two sentences mean the same thing, and it is not a proof that an unseen sentence is safe.

Measured residual, outside the 49:

- "You find a ribbon beneath the board." → `PASS`
- "You discover a ribbon beneath the board." → `FAIL`
- "You notice a crack in the board." → `PASS`

Weak `find` / `notice` / `spot` ignore a new noun unless the head is in the consequential set. That protects cracks and wax seals. It also misses an unlisted portable object in the same frame as the silver key. Stronger verbs do not have that hole.

Other limits:

- A grammatical shape that matches none of the frames can still assert a new fact.
- Restricted secrets are caught when the caller passes them, or when a frame matches (`secretly serves`, `GM_ONLY`, an underscored identifier). The quarantined projection does not contain the secret catalog, so a hidden sentence with no frame can pass the new check.
- The combined gate still false-rejects P1 and S21 through older rules.
- `REVIEW_REQUIRED` is fail-closed here, but a future caller that treats it as displayable text would be wrong.
- No live model output from this cycle was classified. The corpus is hand-built. Real provider prose can leave the frames.

Player-facing narration is still unsafe. A pass on this gate is not permission to show the sentence.
