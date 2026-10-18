# 10 — Conversational Continuity

`_best_exchange` still searches delivered wording. Winners that share a speaker and a proposition id collapse to one subject. Winners with different ids stay ambiguous, including when they share vocabulary.

`_REPEAT` now recognizes "put that another way", "say that another way", and "in another way", which the expression layer already treated as paraphrase requests. The first qualification asked "Put that another way" and received an ignorance line because continuity did not bind the prior sentence. That transcript is preserved. The final primary turn 4 bound the road sentence, attempted a paraphrase, and fell back when the candidate renamed the road.

Genuine ambiguity in the final sample asks "Which earlier remark do you mean?" and makes no expression call. The clarification that follows quotes the sentences for the narrowed subject.
