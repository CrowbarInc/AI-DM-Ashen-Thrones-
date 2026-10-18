# 04 — Source-Level Root Cause

Authorized propositions already came from resolver topics, prior delivered speech, and the host fallback. `build_expression_contract` in `game/expressive_dialogue.py` is where the R3 contract is built. `validate_expression` decides adoption. `apply_expression` calls the provider once and returns the generated line only when validation adopts it. `seal_host_speech` remains the delivery boundary. `record_delivered_exchange` stores the delivered line.

The characterization miss had a specific cause. The validator treated every token outside a closed feeling list as a new claim. "Everything" in "everything feels calm and peaceful" was classified as `unsupported_addition` even though the host had already authorized "I prefer the evening." The provider had not been given a host premise. Adding the word to a feeling list would have widened the lexicon without authorizing the meaning.

Equivalent paraphrases became ambiguous because delivered rows were matched on wording. Two sentences from one road fact did not share an identifier, so `_best_exchange` treated them as competing subjects.

The unattended question was a sufficiency gap. A night-watch topic overlaps the question and does not establish that the gate is never unattended. Before this cycle the deterministic path could fall through to "I couldn't tell you." The older live sample could also recite the watch fact as if it closed the question.

"North street" was already rejected by the place-name bigram check. That check remains. Declared aliases are now the only extra substitution the contract allows.

Security sentences inside a preference explanation were already rejected as unsupported tokens. They are now also rejected by an explicit prohibited-category check, so a sentence that mixes a safe feeling with a gate, a promise, or a secret fails as a whole.
