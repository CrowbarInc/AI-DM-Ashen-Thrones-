# 06 — Host Plan Validation

Validation checks the object shape, the act, the relationship form, ambiguity, confidence, and forbidden authority fields.

Addressee grounding uses only names and aliases present in the scene. Zero matches or several matches produce addressee clarification and no fact. A correction with no prior plan asks which question is meant.

Provider source ids that are not on the addressed NPC are recorded as `rejected_source_ids` and cannot be selected.

Action phrasing (`promise me`, `pay me`, `give me`, `grant me`, `attack`, `advance the clock`, `open the gate`) becomes a refusal. No clock, combat, or inventory operation is executed by this module.
