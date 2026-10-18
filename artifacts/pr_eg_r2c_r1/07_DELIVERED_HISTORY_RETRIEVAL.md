# 07 — Delivered-History Retrieval

Actual selection policy: explicit named speaker, otherwise grounded NPC constraint; requested-information compatibility for ordinary affirmative statements; overlap with delivered subject/supplied text, falling back to the original question only to locate speech such as refusals; highest overlap wins; distinct equally scored statements clarify; identical repeated utterances use recency. With no explicit subject, latest statement is used within the constrained speaker. No positive explicit-subject match returns no record.

Topic IDs and adoption provenance are retained in the existing rows. A later uncertainty/refusal does not delete or supersede an earlier disclosure. Only adopted delivered text enters history; rejected/superseded candidates remain excluded by the untouched R2C boundary. Topic identity constrains authored source selection; natural-language subject matching remains lexical and bounded. Arbitrary synonym resolution is not claimed.
