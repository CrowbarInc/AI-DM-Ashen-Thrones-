# 02 — Root Cause and Repair

Primary failure class: **implementation**. The existing owner already had an established-interlocutor path and a third-person pronoun path. It did not apply that path to ordinary first- and second-person speech.

## Earliest incorrect host decision

`addressed_person_nominal` is the earliest wrong value. For S03.3 the address pattern captures the words after "ask" and the complement cut stops at the comma, leaving `you again later`. For S05.3 the tell pattern captures the words before "about", leaving `me more`.

`assess_addressee_grounding` then treats that span as a person name. Its contextual-pronoun branch accepted only a single `him`/`her`/`he`/`she`. `you` and `me`, with or without continuation words, fell through to the unmatched-nominal result: clarification, no target, provider id kept only as a candidate.

The model and the active social target had already selected the runner. Grounding rejected that selection before the resolver.

## Repair

Two small coordinated edits, because each layer was wrong for a different reason:

1. `speech_participant_head` in `game/interaction_completion.py`, used by `addressed_person_nominal`. A span that is only a speech-role pronoun plus continuation or politeness words collapses to that pronoun. A real name or role is kept. Leading you/me/my/your is dropped only when other identity words remain, and trailing continuation words are dropped after a name. Medial descriptors such as "taller" stay.
2. `assess_addressee_grounding` now treats a one-word first- or second-person role with the same present-interlocutor rule it already used for him/her. The pronoun is never stored as an NPC id. First person means the player is the grammatical recipient; the addressee is the established, still-present participant when the existing uniqueness rules allow it.

No second decision system was added. The phrase list is a closed class of grammatical adjuncts, not the S03.3 or S05.3 sentences.

## Why this generalizes

Any address the existing patterns already extract is reduced before name matching. "you again later", "me more", "ask you later", "tell us more", and "the sergeant again" share that reduction. Second person with a unique established, present participant resolves to that participant. The same words with two present people and no established participant still clarify. An explicit name still wins, including when it conflicts with the old focus. A participant who is no longer in the visible roster cannot be selected, because `_active_npc_id` already requires presence.

Subject matter is untouched. Grounding returns a person id, an eligibility, and a provenance. It does not copy the model's subject into a new fact.
