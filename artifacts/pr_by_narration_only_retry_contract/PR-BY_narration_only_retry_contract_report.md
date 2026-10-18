# PR-BY narration-only retry contract preservation

MODE: BOUNDED DETERMINISTIC IMPLEMENTATION / REGRESSION
LIVE CALLS: 0

Decision: A — RETRY CONTRACT PRESERVATION READY FOR MICRO LIVE

## Inherited defect

PR-BX decision C. P2 attempt 1 selected `narration_only`, returned `{"narration": "..."}`, normalized `declared_claims` to an application-created empty list, and passed declaration validation. Narration validation then rejected the prose. Regeneration feedback told the model to answer again as the same structured envelope with `declared_claims` plus narration, and the authoritative retry context attached `structured_envelope_schema`. Attempt 2 returned declarations and the narration-only parser rejected `unexpected_declared_claims`.

The parser, the empty-declaration normalization, and declaration validation stayed as they were. This cycle changes retry construction only.

## Repair

`regeneration_feedback` already received `provider_response_contract` from the candidate metadata written at parse time. That value is the envelope selected before generation. Retry wording now follows it.

When the stored envelope is `narration_only`, every feedback branch asks for:

`{"narration": "player-facing response"}`

and `retry_authority_context` omits `structured_envelope_schema` and `rejected_declarations`. It attaches `narration_only_response_schema` with the single key `narration`.

When the stored envelope is `structured_realization`, the previous declaration feedback and schema remain.

Retry construction does not call `select_provider_response_envelope` or `project_turn_local_operation`. It does not reread the player text, the response operation, the declaration expectation, or consequentiality to pick a new contract.

## Measured retry contract

Narration-only retry expected keys: `narration`
Narration-only retry `declared_claims` exposed: NO
Narration-only retry `structured_envelope_schema` exposed: NO

Structured retry behavior: preserved. P1 and P3 retries still expose `declared_claims` and `structured_envelope_schema`.
Consequential retry behavior: consequential realization still selects `structured_realization`, and that retry still uses the structured declaration contract.

The PR-BX baker narration, run through `run_preserve_if_valid` against the P2 decision, still fails narration validation as `unauthorized_resolution_decision_fact`. The retry feedback for that failure is narration-only. See `pr_bx_retry_feedback_snapshot.json`.

## Tests

Focused PR-BY: PASS, 22 passed, 0 failed.
PR-BW focused regression: PASS, 26 passed, 0 failed.
Retry/regeneration slice: PASS, 47 passed, 0 failed.
Broad deterministic regression: PASS, 180 passed, 0 failed.

No live model or API calls.

## Next step

STOP. Do not run the live gate. The next independent-review cycle decides whether to rerun a narrow P2 live probe. Do not automatically rerun P1 or P3.
