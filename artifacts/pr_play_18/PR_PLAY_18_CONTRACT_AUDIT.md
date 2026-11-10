# PR-PLAY-18 contract audit

Pre-repair capture: before_request_sanitized.json and context_measurements.json are assembled through actual New Campaign → Start Campaign code with deterministic fixtures and mocked SDK transport. The full local payload was inspected for this audit but is excluded from review packaging because technical analysis needs sizes and contracts, not campaign secrets. No developer-role messages, tools, functions or structured-output definitions were present. Roles were system/system/user.

The first system message explicitly said: “Return valid JSON only with this one-call realization envelope”, followed by declared_claims, narration and player_facing_text. The second system message required selected_entries only. The JSON user payload also supplied legacy narration instructions, response_policy, narrative_plan and authority/declaration scaffolding. No text.format, response_format or schema was sent. This is contradictory instruction construction and missing schema enforcement, not substitution of a correct schema inside the adapter. There was no pre-existing provider JSON Schema for PR-PLAY-13; its contract was expressed in prompt text and the strict Python renderer validator.

| Contract element | Renderer expects | Before repair provider requirement | Result / repaired requirement |
| --- | --- | --- | --- |
| Response type | Presentation plan | Legacy system envelope plus plan system instruction | Mismatch → dedicated plan instruction |
| Selection field | selected_entries only | selected_entries versus declared_claims/narration/player_facing_text | Mismatch → selected_entries required in strict schema |
| Catalog identifiers | Local authorized public IDs | Plan instruction enumerates IDs; legacy source claims also present | Ambiguous → per-entry catalog_id enum |
| Presentation variants | Own entry's approved variant_id | Plan index enumerates variant_ids; no schema | Prompt-only → paired per-ID variant enums |
| Arbitrary narration | Prohibited | First system explicitly requires narration | Mismatch → excluded by prompt/schema and validator |
| Consequential outcomes | Engine-authorized only | Legacy narration/proposal lanes coexist | Conflicting lanes → only public selections; engine retains authority |

Repaired schema: opening_plan_text_format supplies Responses API text.format with type=json_schema, name=opening_presentation, strict=true. Root required=[selected_entries], additionalProperties=false; selected_entries is an array with minItems=1/maxItems=24. Each anyOf branch requires only catalog_id and variant_id, additionalProperties=false, with catalog_id constrained to one local public ID and variant_id to that entry's approved variants. Required coverage, duplicates, ordering and disclosure remain renderer checks. These semantic constraints deliberately remain engine-owned; schema validity alone never authorizes publication.

Repaired outgoing roles are system/user. The system contains the selection instruction plus required/order/variant index. The user contains only scene_opening response-type metadata and opening_public_choices (public IDs and approved text variants). No legacy narration payload is forwarded. Host-authored authority data is not exposed as provider-editable output. Parser, schema and renderer use the same catalog created once for this request. The SDK transport capture and separate real-SDK/in-memory-HTTP test establish schema preservation through serialization.

Root cause: incomplete integration of the opt-in renderer at the provider request boundary. High confidence for current/source-snapshotted integration defect; limited confidence about the exact historical wire contents because that capture is missing. The evidence supports an application contract defect, not a claim that the model ignored a coherent enforced contract.
