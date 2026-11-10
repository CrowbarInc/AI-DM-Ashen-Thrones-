# Validation pipeline integrity

`validate_prelude` still does three things, in this order:

1. Shape checks (string, length, complete sentence, no duplicate anchor).
2. `validate_generated_response`, which includes mechanical claims and authoritative-rule grounding.
3. `validate_consequential_narration` on `authority_from_anchored`.
4. `apply_consequential_gate`.

Combination rules:

- A consequential `PASS` does not change `hard_valid`. A legacy rejection stays a rejection.
- A consequential `FAIL`, `REVIEW_REQUIRED`, or `VALIDATION_ERROR` sets `hard_valid` and `contract_satisfying` false. The preview then uses the deterministic fallback.
- An exception in the consequential check is stored as `VALIDATION_ERROR` and blocks the prelude.
- Neither layer writes inventory, clues, conditions, quests, or the player-facing response. Tests compare the contract and the resolution before and after.
- `game/api.py`, `game/gm.py`, and `game/exploration.py` do not import the consequential module or `preview_anchored_investigation`.

The geography repair and the debris repair sit inside the legacy layer. They remove two false rejects. They do not disable the layer. Keys, currency balances, ungrounded places, and hidden passages still fail there. The consequential layer still rejects the ribbon find even if a future legacy change missed it.

No validation layer grants a mechanical result. A passing audit is not permission to show the sentence to a player. `preview_anchored_investigation` still requires `enabled=True` and still marks the artifact `review_required`.

Quarantine flags were unset for the regression (`ASHEN_QUARANTINE_INVESTIGATION_NARRATION` and `ASHEN_QUARANTINE_NARRATION_LIVE`). The runner does not turn them on.
