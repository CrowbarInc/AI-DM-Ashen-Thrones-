# C21 live Turn 5 and historical malformed incidental persons

Root cause is documented here before the personhood change. Strings are the ones stored in the gate and in the C21 live session, not paraphrases.

## Turn 5 trace

Source: `artifacts/pr_br_continuation21/live/20261002T101405Z/turns.json`, turn 5. Interpretation calls on that turn: 0. The structured interpreter was not invoked.

Raw player input:

> I nod at the tavern runner and say, "Thank you for the guidance. I will make my way to the inn near the market square for rest and warmth first." Then I proceed toward the town gates, aiming to enter Cinderwatch and find the inn to see if I can barter or earn a meal and shelter, while keeping an eye out for anyone who might share useful information about the missing patrol.

Deterministic extraction: `explicit_discourse_binding` in `game/interaction_completion.py`. `_ADDRESS_RE` treats `find` as an address verb. `_complement_cut` stops at `if`. The captured span is `the inn to see`. No catalog interlocutor matches it. It is not a pronoun, so it is proposed as a new person.

Structured interpretation: not invoked.

Candidate span: `the inn to see`.

Candidate type: incidental person.

`referential_person_nominal("the inn to see")` returned `inn to see`.

Person-likeness: `person_shaped` returned true.

Scene plausibility: `scene:populated`.

PR-BN: `pr_bn:accepted`.

Construction: status `bound_incidental`, entity `inc_ec1197ac5e`, label `inn to see`, `explicit_new_interlocutor` true.

Persistence: the incidental record was stored. Discourse committed that id as the active interlocutor. Operation on the turn was `act`. The emitted narration described the market and did not give the fragment a line of dialogue. Gameplay effect: the tavern runner was displaced, and the non-person remained the discourse pointer into turn 6.

## Why it qualified as a person

The accepting check is `referential_person_nominal`, specifically the head test that used the last content word.

1. `_content_words` drops tokens of length 2 or less, so `to` disappears. The content words are `inn` and `see`.
2. The head is `words[-1]`, which is the infinitive `see`, not the noun `inn`.
3. `see` is not in `_FINITE_RE`, `_ABSTRACT_HEAD_RE`, or `_INANIMATE_RE`.
4. The span starts with `the`, so the determiner heuristic accepts the shape.
5. `person_shaped` is a negative test: it returns true unless that same last word is on the short inanimate list. `inn` is not on that list either, so `the inn` alone also passed.

A nominal shape was treated as a person. The place noun was never the head that the check looked at.

## Historical malformed candidates

Gate session `artifacts/pr_br_full_gate/20261002T021950Z`. These were accepted and persisted before the C21 referential check. Later turns that only repeat the label through `identity:discourse` are continuity of the same bad record, not a second extraction.

| Source | Raw player input (abridged) | Extracted candidate | Extraction | Shape | Why it was accepted then | Persisted | Gameplay impact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A5 | ask the exact coin of that modest fee so I can pay it | `exact coin modest fee so i` | address `ask` | determiner noun plus `so I` clause | head not on the inanimate list | yes | pass; generation compensated |
| A9 | ask the first local I pass where a traveler can get a bed | `first local i pass` | address `ask` | noun plus player finite clause | head not on the inanimate list | yes | runner answered a new local |
| B5 | I lean in, matching the captain's low voice | `i lean in` | vocative / clause start | pronoun plus finite verb | head not on the inanimate list | yes | pass; label stuck in later discourse |
| C2 | scan the gate approach for the crate yards | `for crate yards` | address `for` / preposition fragment | preposition plus place | head not on the inanimate list | yes | pass after retry |
| C8 | which face they lingered on | `they lingered on` | address `face` | pronoun plus finite verb | head not on the inanimate list | yes | look became stranger speech |
| D3 | listen toward the underbrush for whatever is moving out there | `underbrush for whatever is moving out there` | address `toward` | place plus clause | head not on the inanimate list | yes | inspection collapsed to wear |
| D7 | walk toward the still patch of brush at a steady pace | `still patch brush at steady pace` | address `toward` | place/region fragment | head not on the inanimate list | yes | evasive-figure failure |
| C21 live T5 | find the inn to see if I can barter | `the inn to see` | address `find`, cut at `if` | place plus purpose infinitive | last content word `see` is not inanimate; `inn` is not on the list | yes | persisted; displaced the runner; did not speak |

Also captured and not persisted as an incidental person:

| Source | Span | Result |
| --- | --- | --- |
| A3 | `the gate` | unresolved, `proposal:not_a_person` |
| B4 | `the crowded gate` | unresolved, `proposal:not_a_person` |
| B10 | `the quieter fringe of the square` | unresolved, `proposal:not_a_person` |
| C6 | `the crowd` | unresolved, `proposal:not_a_person` |
| C21 live T2 | `here at Cinderwa` | proposed, then bound canonical gate serjeant |

C21's referential check already rejected the clause, pronoun, and preposition rows in deterministic tests. It did not reject `the inn to see`.

## Mechanism cluster

One family, three surface shapes.

- Greedy address capture. `find`, `toward`, `face`, and `ask` keep the following words until a complement such as `if` or `where`. A purpose infinitive stays inside the span.
- Last-token head. `to` is discarded as a short token, so the infinitive verb becomes the head. Participial and prepositional modifiers can also hide the real noun: `the porter by the gate` failed before this change because the head became `gate`.
- Negative personhood. Anything whose computed head was absent from a short inanimate and abstract list was a person. Places missing from that list (`inn`, `market`, `room`, `tavern`) passed even with no infinitive.

Not a separate architecture. The same nominal-shape test let clause fragments through in the gate and let the place-plus-infinitive through after C21.
