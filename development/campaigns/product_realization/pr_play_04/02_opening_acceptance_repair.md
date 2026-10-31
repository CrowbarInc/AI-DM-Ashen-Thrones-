# 02 — Opening Acceptance Repair

## Existing success contract

The opening operation is `scene_opening` through the existing `structured_realization` path. `response_type_gating` already requires `scene_opening`. `final_emission_validators.candidate_satisfies_scene_opening_contract` is the existing scene test. It rejects empty text, generic fallback wording, answer-filler, and text that does not establish a scene. This pass does not add paragraph counts, NPC introductions, or other new narrative rules. `validate_opening_output` was not adopted as a stricter gate.

A completion may mark the campaign started only when all of the following hold:

1. The existing structured-output path did not leave `structured_contract_failure` or `structured_output_rejected`.
2. The final text satisfies `candidate_satisfies_scene_opening_contract`.
3. Provenance and authorization are not `safe_nonresolution`.
4. The text is not the generic information-request line.
5. The payload is not a provider fast-fallback or a budget refusal.
6. The completion function returns the normal success payload, not the opening-failure response.

## Exact defect

Requested response `scene_opening` was mapped to expected resolution `answer` and recovery mode `grounded_information_request`. The narration catch-all then called `run_preserve_if_valid`. That sealed `safe_nonresolution` (“No one here can answer that from what is settled here.”) and cleared the visible rejection. Immutable delivery prevented the later emission gate from correcting it. Completion committed that seal as the opening.

## Modified functions

All in `game/api.py`:

- Narration catch-all inside `_build_gpt_narration_from_authoritative_state`. If the operation is a `scene_opening` and structured rejection is already set, `run_preserve_if_valid` is not called. Ordinary unresolved non-openings still enter it. A valid opening that has no structured-failure flag still seals as `initial_generation`.
- `_opening_operation_required`, `_opening_response_rejection`, `_opening_failure_response`.
- `_complete_opening_turn_persistence_like_chat` checks the rejection only when `mark_campaign_started` is true, and returns the failure response before `save_world`.

## New acceptance behavior

Failure response, HTTP 422, status `opening_failed`:

> The campaign opening could not be generated. No gameplay turn was completed. You may try starting the campaign again.

The body includes `opening_failure_reason`, `campaign_started: false`, and `gameplay_committed: false`. It has no `gm_output` and no raw provider error. A budget refusal stays the existing HTTP 409 `blocked` response and `PLAYTEST_STOP_MESSAGE`. HTTP 503 is not used, so the UI does not add the upstream-preflight disclaimer. `static/app.js` already displays `data.error` for this non-503 failure. No UI redesign.

Stable reasons include `missing_structured_envelope` when that code is already on the metadata, `structured_contract_rejected`, `provider_opening_not_delivered`, `safe_nonresolution`, `generic_information_request_fallback`, and the existing scene-contract reason token. Arbitrary exception text is not copied into the reason.

## Fallback handling

A generic information-request fallback does not satisfy `scene_opening`. `safe_nonresolution` does not. An empty-output repair that becomes the generic ask does not. A rejected structured response stays rejected. The opening identity is the `mark_campaign_started` completion, not a substituted answer.

Ordinary non-opening `safe_nonresolution` is unchanged. `test_ordinary_information_fallback_is_not_treated_as_an_opening` still accepts that line for an observe/answer turn.

## Structured validation

Malformed JSON, incomplete envelopes, missing envelopes, and empty output still fail the existing parser or scene contract. No schema, prompt, declaration, or evidence check was relaxed. A paraphrase of authored facts can still fail `undeclared_consequential_claim` when `declared_claims` is empty. The valid control uses narration that restates authorized seed sentences, which the existing audit already accepts.
