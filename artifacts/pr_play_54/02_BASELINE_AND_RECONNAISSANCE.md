# Baseline and reconnaissance

## A. Commit

`d40f1ed198236c604085f1c842ead267a8104ce2`

`fix: restore clarification recency and resolve planner audit false positive`

## B. Working tree

The tree was already dirty before this cycle. That includes unrelated modifications under `game/`, `handoff/`, and many `artifacts/` trees. This cycle did not revert those files and did not commit. The regression runner restored three files the suite rewrote:

- `artifacts/pr_play_49/evidence_performance.json`
- `artifacts/pr_play_47/evidence_performance.json`
- `artifacts/pr_play_52/integration_results.json`

## C. Relevant files

PR-PLAY-53 evidence: `artifacts/pr_play_53/`, especially `06_FABRICATION_VALIDATION.md`, `verdict.json`, and `09_TEST_RESULTS.md`.

Quarantine: `game/quarantined_investigation_narration.py`.

Prelude gate: `game/anchored_investigation_narration.py`.

Previous checks: `game/immutable_valid_response.py` (`validate_generated_response`), `game/mechanical_claims.py`, `game/proposition_authority.py`, `game/authorized_information.py`.

Authorized projection: `game/offline_investigation_projection.py`, `game/narration_authorization.py`.

Characterization tests: `tests/test_pr_play_53_quarantined_live.py`, `tests/test_pr_play_49_anchored_narration.py`, `tests/test_pr_play_51_geography_grounding.py`.

## D. Validation architecture before this cycle

`validate_prelude` checked shape, length, and exact anchor duplication, then called `validate_generated_response`. That function rejects bounded mechanical frames (`you acquire`, `you receive`, possession in a pack) and some ungrounded world rules (`the hidden passage opens`). It does not read `resolution["success"]` for the success/failure narration regex. The success regex is combat-shaped (`you succeed` is present, but the mechanical-success flag is not taken from `resolution["success"]`).

A prelude with `hard_valid` true is still only `heuristic_pass_pending_review`. The quarantine hook can attach it to an evidence record. It does not replace the player response.

## E. Inputs

The anchored contract supplies status, success, revealed clue text, previously known text, public observations, and engine status sentences. Hidden fixture fields are not copied into the prelude request.

## F. Outputs

`validate_generated_response` returns `hard_valid`, reason codes, and a mechanical-claim audit. The prelude preview returns `used_fallback` and a diagnostic: `heuristic_pass_pending_review` or `semantic_rejection`.

## G. Failure classes PR-PLAY-53 recorded

| Line | Previous result |
| --- | --- |
| You find a silver key beneath the board. | accepted |
| You recognize the culprit immediately. | accepted |
| The tavern runner confesses that he sold the patrol route. | accepted |
| You succeed in uncovering the patrol route. (failed check) | accepted |
| The silver key is now yours. | accepted |
| You read that the patrol took the northwest mud track past the crates. (no clue) | accepted |
| You acquire a brass compass. | rejected, `unsupported_mechanical_claim:items_added` |
| The hidden passage opens before you. | rejected, `ungrounded_authoritative_rule` |
| A silver key now rests among your possessions. | rejected, `unsupported_mechanical_claim:items_added` |

## H. Known regressions

PR-PLAY-53 focused suite: 426 collected, 423 passed, 3 failed, 0 skipped. The three failures were already present:

- `tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution`
- `tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues`
- `tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues`

Those three failed again in this cycle. No new failure appeared.
