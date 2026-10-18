# 06 — Candidate Validation

Validation is deterministic token closure against the contract. A second model is not consulted.

Shared checks reject empty or overlong speech, more than two sentences, internal-rule voice, and numbers that were not authorized. Faithful paraphrase and simple explanation require every authorized content token to be covered by the candidate or by a closed synonym, and every candidate content token to be covered by the source. Real hedges such as “heard” or “may” must survive. “Definitely,” “certainly,” and “I know” are epistemic strengthening. A verbatim copy is rejected when the player asked for a rewording. The delivery frame “Word is,” may be dropped.

Place names are not free synonyms. A content bigram whose head is road, street, gate, bell, or ferry must remain exact, except that a spatial modifier in {beyond, outside, past, beside} may be replaced by another word from that set while the head noun stays. “North road” therefore cannot become “north street.” “Beyond the gate” may become “past the gate.”

Incidental characterization allows the authorized preference plus a closed subjective lexicon, and it requires a reason cue with “because” or “when.” Morning and evening cannot replace each other. Uncertainty and refusal allow the question’s own words plus a small closed lexicon, require the uncertainty or refusal marker, and reject “because,” “but,” and “since.” An extra sentence without the marker is rejected. Typographic apostrophes are folded before tokenization so “don’t” is the same word as “don't.” Inflection folding applies only inside the uncertainty and refusal closure check.

The validator cannot understand arbitrary safe prose. A category whose output cannot be closed against the contract is rejected and the host fallback is used. That is the intended limitation, not a second semantic model.
