# 03 — Presentation Plan Contract

The only accepted object is:

```json
{"selected_entries": [{"catalog_id": "rc_example", "variant_id": "authored"}]}
```

There is no narration field, no declaration text, and no state-update field. Extra keys are rejected. A narration-like key is `arbitrary_narration_field`. An authority, disclosure, or mutation key is `model_supplied_authority`. Any other extra key is `unsupported_field`.

## Rejection reasons

| Condition | Reason |
| --- | --- |
| Unknown catalog id, including a hidden id that exists only outside the catalog | `unknown_catalog_id` |
| Unknown variant | `unknown_variant_id` |
| Repeated catalog id | `duplicate_selection` |
| Missing required entry | `missing_required_entry` |
| Required entries out of catalog sequence | `invalid_ordering` |
| More than 24 selections, or a malformed object | `plan_bound` or `plan_schema` |
| Empty selection | `empty_opening_render` |

Rejection stores a reason code, not the model text. The opening failure response remains the existing fixed message. The injected sentence is not copied into that response.

A presentation selection is not a gameplay command. Movement, checks, inventory, quests, injury, faction, and time are not representable as plan fields.
