# Referential head

Files: `game/incidental_entity.py`, `game/interaction_completion.py`, `tests/test_pr_br_continuation21c_referential_head.py`.

The referential head is the right edge of the prenominal cluster. The cluster stops at the first postnominal boundary: a preposition, a relative pronoun after a noun, an infinitive, a participle that has a complement, a locative adjunct after a noun, or a coordinated second nominal. Determiners and prenominal adjectives are not the head. The last token of the original span is not the head.

`the muddy lane northwest of the crates` stops before `northwest`. The head is `lane`. `northwest` is a locative adjunct, not a non-person vocabulary entry. `lane` is not on the non-person list either. Its personhood is unknown, so no person is created.

Compounds are head-final. `gate guard` denotes `guard`, which is already a person. `stable hand` keeps both words, because `hand` alone is not a person. `notice board` denotes `board`, which is not a person.

Unknown heads abstain (`proposal:personhood_unresolved`). They are not stored and they do not restore the previous interlocutor. Agentive shape (`-er`, `-or`, `-ist`) still accepts an unlisted role such as `lamplighter`. A short social-category set covers roles that have no agentive ending (`woman`, `guard`, `merchant`, `sentry`, and the consequential roles the existing tests already reject). That set is not an occupation encyclopedia.

A model span is rechecked by the same head function. A person label does not override a non-person or unknown head.

`to see if the innkeeper` recovers the person in the purpose clause. `the inn to see` stays a place. `the inn and the porter` has no single head.

Non-person list additions: 0. `northwest` and `lane` were not added.
