# 05 — Generalization and Ambiguity

These fixtures were written with the repair. They are related variations, not independent held-out evidence and not an Ashen Thrones Gameplay Benchmark result. Names are Porter Hale, Clerk Ivo, and Usher Bel except where a historical replay must use the runner.

## Speech-role variations

Checked forms include you, me, I, we, us, your, my, you again, tell me, ask you, speak with you, tell me more, and ask you later, plus capitalization, punctuation, a quoted "Tell me more", and a longer multi-clause sentence. In each established-addressee case the target stayed the active participant, or an explicit name when one was present. "I" and "me" never became an NPC id. "my clerk" and "your clerk" kept the clerk and dropped the possessive.

## Explicit addressee change

"I turn to Clerk Ivo and ask what happened" while Porter is active selects Clerk Ivo, provenance `explicit_canonical`, conflict `resolved_by_explicit_wording`. Porter is not kept.

## Multiple recipients

"Can you tell me what happened?" with Porter and Clerk present, no active participant, and a provider candidate of Porter does not select Porter. Eligibility is `requires_clarification` and mutation is false.

## Absent NPC

A session still naming Porter, while only Clerk and Usher are visible, does not return Porter for "Can you tell me more?". The choice list is the two people still present.

## Third-party reference

"What did Clerk Ivo tell you?" while speaking with Porter keeps Porter. The extracted nominal is "you". Clerk Ivo is not substituted as the recipient.

## Subject ambiguity

"Can you tell me more?" with Porter established resolves Porter and leaves no subject field on the grounding result. S05.3, above, is the historical instance: recipient resolved, subject not answered, no new rumor text emitted by the decision.

## What still clarifies

"someone nearby", "either clerk", and an unknown "Warden Cole" stay unresolved with mutation false. A single visible "him" still uses `unique_contextual`. "What did she mean by the road?" does not inherit the active speaker. A provider id that disagrees with the established participant on a bare "you" clarifies instead of switching people.
