# 15 — Bounded Improvisation Compatibility

R4 does not grant improvisation authority. PR-EG is not started.

## Boundaries that stay

- Canonical facts and revealed clues stay on the resolver. The lantern mark is delivered only by `discover_clue`.
- Player-visible prior lines can be quoted by a GM answer. Turn 4 quotes Mara’s north-road sentence because it is already public.
- NPC knowledge is not invented to fill a gap. When speech authority is `none` and no topic is revealed, the safe line or a validated uncertain line is what the player hears. Hidden facts are not added to the prompt as answerable content.
- Incidental color is not persisted. “I don’t know.” in case B was a generated line accepted by existing validation. It was not written back as a world fact.
- Consequential changes still require mutation eligibility and a resolver. Clarification bookkeeping is not a world tick.

## Where PR-EG could attach later

The authorization record already separates candidate targets, provenance, mutation eligibility, and operation eligibility. A future non-persisted incidental proposal can hang off this record without becoming `target_id` or `mutation_eligibility`. The narration predicate is the place that would later allow a bounded line when the plan is `genuine_uncertainty` and validation has an allowed subjective opening. R4 leaves that plan on the provider path on purpose.

`authoritative_answer_available` with speech authority `none` and no topic is an inconsistent resolver signal. PR-EG should not treat it as permission to invent the missing fact. It needs a resolver decision about whether an answer actually exists before any new speech lane opens.

## Explicit non-goals

- No new improviser, no second interpreter, no campaign-initialization flow.
- No blanket refusal of unknown questions.
- No use of a provider id as proof that a person reference is resolved.
- No undo of an executed world tick when the player corrects the wording afterward.
