# PR-BW Provider-Visible Schema Analysis

## Repository Schema

The envelope is prompt-defined in `game/gm.py` and parsed in `game/structured_player_output.py`. Runtime validation lives in `game/gm_resolution_decision.py`.

Relevant source behavior:

- `classify_model_output` treats a dict with `declared_claims` and `narration` as a structured envelope.
- `_parse_gm_response` stores `metadata.realization_envelope.declared_claims`; when structured claims are required, a missing non-list declaration field is a failure.
- `realization_envelope_from_mapping` requires `"declared_claims"` to exist, requires it to be a list, and allows that list to be empty.
- `validate_declared_claims_against_decision(None)` treats missing declarations as no structured contract; `[]` is a present valid contract with no claims.

## Provider-Visible Schema

Preserved provider request files contain `provider_input` only. There is no saved `response_format`, `json_schema`, or strict provider-side structured-output configuration object. The provider-visible schema is the JSON example embedded in the system prompt.

Configuration result:

```json
{
  "response_format_present": false,
  "json_schema_present": false,
  "strict_provider_schema_present": false,
  "provider_visible_schema_source": "system prompt JSON example"
}
```

## Field Requiredness And Optionality

The prompt asks for valid JSON with a "one-call realization envelope" and shows all top-level fields. It does not mark `declared_claims` optional. The parser requires `declared_claims` as a list when structured claims are required. Empty list is permitted.

| Field | Provider example | Runtime acceptance |
| --- | --- | --- |
| `declared_claims` | Array shown first | Required as list for structured contract; `[]` valid |
| `narration` | String | Required for structured envelope |
| `player_facing_text` | Same string as narration | Legacy compatibility |
| `tags` | String array | Optional-ish, defaults to [] if malformed/missing |
| `improvisation_proposals` | null or array | Optional |
| `scene_update` | null or object | Optional |
| `activate_scene_id` | null or string | Optional |
| `new_scene_draft` | null or object | Optional |
| `world_updates` | null or object | Optional |
| `suggested_action` | null or object | Optional |
| `debug_notes` | string | Optional-ish, fallback text if absent |

## Declaration Surface

Declaration fields visible to the model:

- `declaration_id`
- `declaration_mode`: `realize|propose`
- `source_claim_id`
- `premise_claim_ids`
- `semantic_identity`
- `provenance_requested`: `authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim`
- `epistemic_status`: `established|inferred|hypothesis|unresolved|possible`
- `modality`: `established|possible|hypothetical|unresolved`
- `realization_role`: `MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE`
- `relation_kind`: `observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead`
- `text`

This is a rich authorship vocabulary. By contrast, narration receives only `"narration": "string"` in the schema example.

## Ordering

The schema appears in this order:

1. `declared_claims`
2. `narration`
3. `player_facing_text`
4. `tags`
5. `improvisation_proposals`
6. `scene_update`
7. `activate_scene_id`
8. `new_scene_draft`
9. `world_updates`
10. `suggested_action`
11. `debug_notes`

This encourages declaration-first reasoning. That can help semantic control, but on narration-only turns it also keeps consequential authorship in view before the model reaches the prose answer.

## Footprint

Measured from PR-BV P2 provider request:

```json
{
  "system_prompt_total_chars": 9568,
  "envelope_schema_block_chars": 2619,
  "declared_claims_schema_chars": 847,
  "narration_schema_chars": 25,
  "structured_claim_rule_chars": 1251,
  "bounded_improvisation_rule_chars": 910
}
```

The declaration schema alone is about 34x the narration field's schema footprint. The structured claim rule is another 1,251 chars about when and how to declare consequential propositions.

## Empty Declaration Representation

The main provider-visible example shows an array with an object, not `declared_claims: []`. Empty declarations are valid in runtime evidence, but the primary schema does not positively frame an empty list as normal for narration-only turns.

## Examples

No separate few-shot examples were found in the preserved provider-visible prompt. The JSON example is a shape example with a populated declaration object.

## Provider Translation

No evidence of provider schema flattening, strict JSON schema required arrays, defaults, nullable unions, or provider-side optionality transformation appears in the preserved request. The important translation is from repository prompt constants into one system-message schema example. Provider-side descriptions are ordinary prompt text, not typed schema descriptions.
