# Implementation summary

Files: `game/incidental_entity.py`, `game/interaction_completion.py`, `tests/test_pr_br_continuation21b_referential_personhood.py`.

`referential_nominal` and `referential_person_nominal` are separate. A place can be a nominal and still be refused as a person.

Before the head is chosen, the span drops a purpose infinitive, a participle, a locative tail, and an `of` complement that still leaves a noun. `one of the travelers` is kept, because `one` is not a content head. A player-pronoun finite clause abstains. A `who` relative is cut.

The head is still the last remaining content word. Personhood rejects known place, object, route, abstract, and action heads. Any other common-noun head may be a person. There is no occupation whitelist.

A captured address that fails this check sets an explicit new attempt, so the previous interlocutor is not restored. It is not stored.

The live leak is the remaining last-word rule. `the muddy lane northwest of the crates` loses `of the crates` and keeps `northwest` as the head. `northwest` is not in the non-person set, so the route was stored.
