# Publication-state semantics

`session.last_publication` is the latest completed gameplay sentence, not the last accepted live expression and not the last provider attempt.

A composer (`integrated_play.commit_integrated` or `bounded_improvisation.conversation`) that already stored the sentence being delivered keeps its provenance, including `dialogue_accepted`. The note stamps `turn` and `campaign_run_id` onto that record when they are missing. `campaign_run_id` is the existing volatile identity key. An earlier revision used `campaign_id`. Paired historical comparisons do not strip that name, so two campaigns with the same sentence compared unequal. The stamp was renamed before the final regression.

If the stored sentence is any other sentence, the note replaces the record. A rejected expression is not copied forward as an acceptance. `dialogue_accepted` is true only when this turn's audit decision is `adopted`, fallback was not used, and any candidate text is inside the visible sentence.

`session.last_background_expression` remains the last expression attempt. A missing audit on a later turn leaves the prior attempt in place. When an audit exists, `adopted` is true only for an adopted, non-fallback decision.

Empty text does not clear the prior record.

A non-mutating interpretation refusal returns before this note. That path is the remaining gap, recorded in `18_LIMITATIONS_AND_RISKS.md`.
