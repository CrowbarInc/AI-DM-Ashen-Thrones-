# Limitations and open risks

The check is still a set of English frames compared with an authority snapshot. It is not a proof that two sentences mean the same thing, and it is not a proof that an unseen sentence is safe.

## Residual classification gaps

- "You notice a ribbon tied to the fence" passes. Perception of a plain-sight object, without concealment or acquisition, is treated as scenery. A real clue delivered that way can pass.
- Geography aliases are a closed list: compass forms, dusk/sundown/sunset/nightfall, patrol/rounds, guard/sentry. "The sentry walks the west road" does not match, because `walks` is not `patrol`.
- Debris is a closed substance list on the lies/contains frames. "You receive a little dust" is still an item claim.
- Unfamiliar marks are detected by mark-words (marking, symbol, glyph, rune, and the rest). A novel clue noun with no mark-word and no concealment can pass under `notice`.
- The stemmer is crude. `leaving` and `leaves` do not always reduce to the same token. Some paraphrases pass only because no frame fires, not because the stemmer proved equivalence.
- `REVIEW_REQUIRED` is conservative for marks and for the two older underspecified lines. A future caller that displays review text would be wrong.
- Restricted secrets are caught when the caller passes them or when a frame matches. The quarantined projection still does not contain the secret catalog.

## Holdout

The holdout was hashed before the validator edit (`24ff35e8f4096e865dcf3ffd6f98a92d18a208e1329c445c33525e5e5fed1495`) and was not revised after the one-shot. Labels were not fitted to failing output, because the one-shot had no mismatches.

The corpus was written in this same session, to the same rules the code implements. It uses new objects and places. It is not a paraphrase of the 49. It is also not an independently authored blind set. The process separation is the hash and the refusal to edit after the run. That is weaker than a second author.

## Other

- No live model prose from this cycle was classified.
- Three older tests still fail. They are outside this validator.
- A dirty working tree predates this cycle. Unrelated files were not reverted and were not claimed as part of the result.
- Player-facing narration remains unsafe. A pass on this gate is not permission to show the sentence.
