# State and quarantine integrity

Covered by `tests/test_pr_play_54_consequential_validation.py` and the existing quarantine file.

| Invariant | Result |
| --- | --- |
| Validation does not modify the anchored contract | passed |
| Validation does not authorize a discovery | the authority object is read-only; restricted fields stay empty on the projection |
| Validation does not change mechanical outcomes | player-path character and mechanical snapshots match the baseline |
| Validation does not modify inventory | character snapshot unchanged when a key sentence and a review sentence are injected |
| Validation does not change conditions | same snapshot comparison |
| Validation does not reveal hidden information | projection test asserts `UNSEEN` and `gm_only` are absent from the authority text |
| Validation does not alter the deterministic player response | facing text matches the no-live baseline |
| A validation failure does not corrupt the completed action | fallback is used; the clue sentence remains the engine sentence |
| Exceptions stay on the prelude audit | a raised checker becomes `VALIDATION_ERROR` and `hard_valid` false |
| Uncertainty is not a player-facing pass | `REVIEW_REQUIRED` and `VALIDATION_ERROR` both force fallback |

`game/api.py`, `game/gm.py`, and `game/exploration.py` do not import the new module. The hook still runs only as a quarantine observer. The live flag default test in the PR-PLAY-53 file still expects zero provider clients when the flag is off.

Injected "You find a silver key beneath the board." now records `semantic_rejection` and `FAIL`. The assembled fallback does not contain the key. The player response does not contain it.
