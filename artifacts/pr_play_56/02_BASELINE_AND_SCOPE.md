# Baseline and scope

Repository commit: `d40f1ed198236c604085f1c842ead267a8104ce2`.

The working tree was already dirty. This cycle did not revert those edits. The narration validator and the quarantine hook were not among the files this cycle changed. `game/expressive_dialogue.py` and `game/provider_budget.py` already contained uncommitted edits. Those edits cover public-fact offerings and opening diagnostics. They do not change `request_expression`, which is the call the quarantine hook uses.

## Validator under test

The validator is `game/consequential_narration_validation.py`.

SHA-256 before the live requests, and again after them:

`ed29349cde1bb641178b01175f608142707dcc21a7d387e4b0f57707a1d0d6b6`

A byte copy was stored at `artifacts/pr_play_56/frozen_validator/consequential_narration_validation.py` before the first request. It matches the file after the run.

The hook calls it from `game/anchored_investigation_narration.py` `validate_prelude`, after the legacy check in `game/immutable_valid_response.py`. There is no separate validation config file. The rules are the constants in the validator module. They were not edited.

Supporting file hashes are in `validator_hashes_before.json` and `validator_hashes_after.json`.

## What PR-PLAY-55 had already shown

Those scores are not treated as proof that live prose is safe.

- 49/49 earlier fabrication lines still failed.
- 40/40 development cases matched their labels.
- 70/70 frozen holdout cases matched their labels.
- 13/13 authorized paraphrases in that development set were accepted.
- 11/11 ambiguous cases were flagged rather than passed.
- Focused regression: 529 passed, 3 previously known failures.
- No provider was called in that cycle.

Known focused failures, left untouched:

- `tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution`
- `tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues`
- `tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues`

PR-PLAY-55 also reported `KeyError: 'hard_validation_attempt_1'` outside the focused suite, in `tests/test_pr_cx_authority_assurance.py` and in some PR-BR continuation files. Those files were not bisected on a clean tree.

## Pipeline this cycle actually ran

Authoritative resolution, then the detached narration projection, then one quarantined expression request, then the frozen validator, then this review. The provider did not resolve the action. A passing validation result was not written into the player-facing line.

## Out of scope

No validator edit. No new provider. No new campaign fact. No player-facing narration flag. No commit.
