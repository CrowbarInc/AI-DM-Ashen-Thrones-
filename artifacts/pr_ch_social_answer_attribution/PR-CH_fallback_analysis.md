# PR-CH Fallback Analysis

Observed final refusal:

`Kiln Tender says, "I cannot answer that from what is settled here."`

The statement is defined in `game.interaction_completion.generic_ask_completion` and used by `game.immutable_valid_response.safe_nonresolution` as a last-resort ask completion.

For the target, this is not genuine uncertainty:
- The authored topic exists.
- The resolver selects it.
- The HTTP run logs clue discovery for `kiln_bank`.
- The authored-answer helper can render the correct answer.

The fallback is structurally safe but unnecessary for this turn. It replaces or preserves non-answer text after a valid authored answer is already available.

First failing boundary: validation/fallback/immutable final emission.

