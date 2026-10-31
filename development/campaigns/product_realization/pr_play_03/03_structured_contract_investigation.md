# 03 — Structured Contract Investigation

**Conclusion:** The host demonstrably rejected its extracted string as plain output. The original provider content and completion details were not retained, so attributing that rejection to the model is unsupported. Primary failure class remains **unresolved**. Recovery has a separate demonstrated implementation defect.

`_opening_scene_normalized_action_and_resolution` assigns scene_opening. `response_type_gating.derive_response_type_contract` explicitly selects the same required type. `gm_resolution_decision.select_provider_response_envelope:4755` selects narration_only only for eligible incidental dialogue with no consequential realization; this opening selects structured_realization. `gm._provider_response_contract_from_payload:4154` selects the system prompt; `_provider_response_contract_from_messages:4170` selects the parser contract by a narration-only system marker. Original rejection metadata confirms structured_realization.

`gm.SYSTEM_PROMPT:202` requests JSON only, with `declared_claims` and `narration`, temporary same-text player_facing_text, optional proposals/state fields, and a detailed declaration example. `opening_scene_realization.merge_opening_instructions:540` requests anchored perspective, observable facts, sensory detail, pressure and playable affordances inside that response. These are expression requirements, not permission to emit bare prose. No demonstrated provider/host format mismatch appears in current source or reconstructed requests. The envelope choice is authority-derived, not chosen by the UI response type alone.

`call_gpt` sends `client.responses.create(model=..., input=messages, max_output_tokens=600)` when accounting is active. **Observed:** formatting is requested in instructions; the owner does not supply Responses `text.format` or a schema. Lack of API enforcement increases reliance on instruction compliance but is not evidence of the historical cause. Changing to a schema without proof would exceed this investigation.

Extraction uses `getattr(resp, 'output_text', None)`, falling back to `str(resp)` if None; it does not inspect individual output items. Empty output_text does not trigger the string fallback. `_safe_json(text.strip(), require_structured_claims=True)` delegates to `classify_model_output`:

* Whole-response JSON fences are removed. A recognized dict with nonempty narration/player_facing_text and no nested envelope is structured.
* A valid structured realization also requires declared_claims to be a list. Later decision/claim validators enforce authority; parser acceptance alone is insufficient.
* Empty input, recognizable damaged envelopes, non-object JSON and bad envelope prose are malformed.
* A non-JSON string without a recognizable response envelope is plain. Required-structured/plain emits **missing_structured_envelope**, empty narration, and both rejection tags. This is a classifier result, not a diagnosis of what the provider generated.

| Explanation | Finding |
|---|---|
| A1 malformed generation | Plausible, unknown. Plain provider prose would reproduce the tag. Original prose absent. |
| A2 extraction loss | Plausible, unknown. Missing output_text could stringify a response object, or usable content could reside elsewhere. No original output-item capture to distinguish. |
| A3 valid representation rejected | No demonstrated valid intended-envelope defect. Whole JSON and fenced JSON accept offline. Prose wrapping an envelope rejects; that violates JSON-only instructions. Original representation unknown. |
| A4 contract mismatch | Not demonstrated. Current system instructions and parser both request structured realization. Original effective messages unavailable, so historical drift cannot be ruled out absolutely. |
| A5 incomplete/truncated generation | Plausible. Output usage equals the default accounting cap (600). Offline `{"declared_claims": [` produces the *same* missing-envelope tag because that partial shape is not recognized by the envelope scanner. Equality to cap is circumstantial, not proof. |
| A6 other | No other mechanism established. Connectivity is not implicated by a completed metered response and was not investigated. |

`parser_controls.json` records all exact controlled strings and outputs: JSON and fenced positive controls accept; plain and partial-declarations inputs both yield missing_structured_envelope; narration-only under structured mode and prose-wrapped JSON yield malformed_envelope. Thirty-eight existing structured/narration-only/retry contract checks pass. None reproduces original generation.

The ledger's completion_status=completed is synthesized by RequestAttempt.finish when dispatch occurred. `call_gpt` does not pass provider status/incomplete_details to it. It cannot exclude A5. Do not change parsing, prompts or output caps based only on this tag or 600-token usage.
