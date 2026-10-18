# Deterministic results

`tests/test_pr_br_continuation21c_referential_head.py` passed, including the matrices below.

Historical malformed spans rejected as people: 22/22. That set is the Continuation 2 list, the recorded gate fragments, and `the muddy lane northwest of the crates`. Historical player turns, including the Continuation 2 Turn 3 sentence: 9/9 did not persist those labels.

`the inn to see`: rejected as a person. Head `inn`.
`the muddy lane northwest of the crates`: rejected as a person. Head `lane`. `northwest` is not the head and is not in the non-person list.

Valid-person controls: 15/15.
Non-person controls: 13/13.
Structural variations: pass (stacked adjectives, compounds, prepositions, participles, infinitives, relatives, direction, possessive, determiners, coordination).
Player-input integration J1–J8: pass.
Raw `/api/chat` stub: pass.
Turn 3 replay: the lane is not a person. The milestone move remains, and it is not caused by that binding.

C18, C19, C20, C21 subject integrity, and Continuation 2 tests passed inside the broader band.

Broader PR-BR band (continuations 12–21c, resolution contract, interaction completion, interpretation proposal, model interpretation, outcome precedence): 270 passed, 0 failed.

Non-person list additions: 0. Social-category forms added so unknown heads do not default to person: 18. Not a substitute for the structural head.

No full-suite run.
