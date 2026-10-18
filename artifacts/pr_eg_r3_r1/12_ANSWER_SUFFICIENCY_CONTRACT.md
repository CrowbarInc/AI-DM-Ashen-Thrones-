# 12 — Answer-Sufficiency Contract

`classify_answer_sufficiency` returns `directly_answers`, `partially_informs`, `does_not_answer`, or `unknown`.

An absence question such as "ever left unattended" or "unguarded", paired with one coverage fact about a watch, guard, sentry, or patrol, and with specific subject overlap, is `partially_informs`. If the authorized fact itself states the absence, it is `directly_answers`. No overlap yields `does_not_answer`. Empty text yields `unknown`.

The host line for a partial answer is the fact plus "I couldn't say whether it is ever left ...". It sets `answer_sufficiency` to `partially_informs`. It does not mark the topic revealed and does not append `revealed_topics`. `_next_topic_to_reveal` still returns None for the absence question. Expression is not generated for that posture.

Final primary turn 10: "Guards watch the north gate throughout the night. I couldn't say whether it is ever left unattended." Final secondary turn 2 uses the same shape for the harbor gate and "unguarded." Neither line says the gate is never unattended.
