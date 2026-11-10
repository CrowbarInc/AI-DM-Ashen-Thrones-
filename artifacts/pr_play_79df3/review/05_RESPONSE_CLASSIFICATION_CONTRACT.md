# Response Classification Contract

No public response schema was added. Completion is not inferred from HTTP 200, from visible text, or from the absence of a state mutation.

## A. Completed gameplay publication

A sentence the engine delivered: accepted speech, a grounded fallback, a deterministic action result, a completed investigation, or an existing clarification or supported read-only gameplay response. It may be non-mutating. `record_completed_publication` writes one event. `note_completed_publication` advances `session.last_publication` only when the existing finalizer delivers that sentence.

## B. Operational refusal

The application could not process the interaction because admission or the interpretation service stopped it. The player may see the safe sentence. It is not a completed gameplay publication.

`OPERATIONAL_REFUSAL_REASONS` in `game/publication_contract.py` is the closed set: provider calls disabled, provider budget stopped, playtest stopped, duplicate request identity, request ceiling, input-token ceiling, output-token ceiling, total-token ceiling, admission or usage accounting unavailable, budget exceeded after a completed request, ledger initialization/change/dispatch/completion/rejection failures, generation diagnostic ledger write failed, token estimate unavailable, provider failure, and model mismatch.

`provider_failure` and `model_mismatch` use failure stage `interpretation_service`. The rest use `provider_admission`.

When the class is present, `record_completed_publication` returns without writing. `api_chat` and `api_action` set `skip_publication_trace`.

## C. Gameplay refusal

Unsupported action, clarification, malformed interpretation, malformed communication, and context leak stay on their existing gameplay publication path. A rejected expression that becomes a grounded fallback is completed gameplay. State stillness alone is not an operational refusal.

## D. Transport or server error

Status 400 and above still record `response_category=error`. They are not converted into a successful gameplay publication.

## E. Incomplete request

A duplicate or a request that never reaches publication does not fabricate a completed gameplay event and does not advance `session.last_publication`.

## Diagnostics kept on the server record

Request and session identity stay on the existing log. The refusal record stores failure stage, refusal category, whether a provider request was sent, gameplay executed false, authoritative state changed false, gameplay publication completed false, player-visible category `operational_refusal`, and recovery eligible true. Prompts, credentials, ledgers, and exception text are not added to the projected HTTP body.
