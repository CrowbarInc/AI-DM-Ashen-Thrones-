# Implementation Changes

Smallest repair on the existing publication contract. No second publication system. No new persistent schema. No public HTTP field.

## `game/publication_contract.py`

- Added `OPERATIONAL_REFUSAL` and `OPERATIONAL_REFUSAL_REASONS`.
- Added `classify_operational_refusal` and `response_is_operational_refusal`.
- `record_completed_publication` accepts `response_class`. When that value is `operational_refusal`, it returns `None` before any write.

## `game/live_chat_interpretation.py`

The not-ok `_blocked` extra now includes `provider_request_sent` copied from `call["sent"]`. The exception return already recorded `sent: true` and reason `provider_failure`. The exception message is not copied into the player response.

## `game/api.py`

`_live_interpretation_block_response` stamps the classification onto resolution metadata and log metadata when the reason is operational.

`api_chat` and `api_action`, after projection, set `request.state.skip_publication_trace` and pass `response_class=operational_refusal` when `response_is_operational_refusal` is true. Duplicate requests still return early with the skip flag.

## Unchanged product files

`game/player_http_boundary.py`, `game/player_http_projection.py`, `game/provider_budget.py`, and `static/app.js`. The frontend already shows `gm_output.player_facing_text` when `ok` is true, so the safe refusal appears as a GM message without a script change.

## New tests

- `tests/pr_play_79df3_harness.py`
- `tests/test_pr_play_79df3_classification.py`
- `tests/test_pr_play_79df3_holdout.py`
- `tests/fixtures/pr_play_79df3_holdout.json`
- `tests/fixtures/pr_play_79df3_holdout.sha256`

`game/api.py` remains a large pre-existing dirty file. This cycle’s edits there are the classification stamp and the two skip checks.
