# 29 — Implementation Readiness

Not started. When a later cycle is authorized:

- Add a host candidate generator beside `game/conversational_referents.py`. Do not replace referent storage.
- Replace the provider operation schema with a candidate-id selection schema behind `ASHEN_UNIFIED_SEMANTIC_PLANNING`, default off.
- Keep `authorize_information_turn`, disclosure, and final sealing. A selected candidate that fails witness or source policy stays unaccepted.
- Preserve `game/dialogue_authority.py` and `game/immutable_valid_response.py`.
- Regression set: this corpus's frozen validation and holdout files, plus the existing forged-referent and disclosure tests. Do not edit those tests to match a new disposition without a separate decision.
- Qualification is a new live run after the gate is wired, not this isolated prototype.
