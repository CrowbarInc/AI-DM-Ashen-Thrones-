# PR-PLAY-25 authority contract

Category A: established public information may support narrowly scoped speech. Category B: authored restricted information retains its existing disclosure policy. Category C: a new price, reward, quantity, obligation or world change requires independent game-state authority and cannot be minted by dialogue.

Eligibility requires all of the following:

* A real resolved, same-scene NPC and an exact matching social target ID, with no selected authored topic, ambiguity, refusal or locked semantic plan superseding it.
* A unique explicit `addressables` row: matching NPC ID and exact NPC name, `kind=npc`, correct `scene_id`, `addressable=true`, matching NPC location. Duplicate subject names/IDs fail closed.
* A string from authoritative current `visible_facts`, full-matching the bounded form `[A/An/The] <exact registered subject> offers/sells/serves/trades <bounded list> [near <location>].` The proposition projects just the listed offerings into `I offer <items>.` It does not authorize the location or facts about the items.
* A complete recognized own-offerings question: offering/selling/serving/available/services variants, including the original approach-and-ask phrasing. Third-party questions, prices, secrets, rewards and compound qualified questions do not match.
* One eligible source only. Numbers, prices, restricted/consequential vocabulary, negation, conditional clauses and unsupported syntax fail closed.

Provenance records the actual scene ID and visible index, exact source text, resolved NPC ID, projected proposition and `own_offerings` relation. It is deterministic derived attribution, not authored entity metadata. The legacy data has no stronger per-fact entity reference; no migration or fabricated authored provenance is introduced. Display-name overlap alone is insufficient: exact grammatical subject, unique registry binding, same scene, positive bounded assertion and relevant question are all required.

Authored topics are never replaced. A selected topic wins through the existing pipeline. Any authored offerings topic blocks this fallback even if restricted or not selected. A restricted topic sharing an advertised item also blocks fallback. Multiple public candidates yield `ambiguous_facts`; ambiguous subjects yield `ambiguous_subject`. Conflicting authored offerings produce `authored_offering_precedence`, never a merge. No public source grants the guard the merchant's commercial knowledge.

The expression provider receives the existing identity/question/proposition/constraints contract. It may reword offering verbs (offer/sell/serve/I've got) while preserving all item descriptions. Content checks still reject new nouns, numbers, prices, rewards, commitments, name substitutions, strengthened epistemic claims and negation. Unsupported output falls back to the authorized host offering sentence and records rejection reasons.

Limits are intentional: arbitrary prose, aliases, pronoun subjects, unregistered actors, globally observable facts, stock/pricing mechanisms and a bare nearby-banner question are not newly authorized. A source phrased only as “shouts offers of...” remains outside this grammar. The captured direct offering sentence is supported. Existing facts need not be rewritten, and no NPC-specific name/item exception exists. This is not unrestricted natural-language understanding or general public knowledge.
