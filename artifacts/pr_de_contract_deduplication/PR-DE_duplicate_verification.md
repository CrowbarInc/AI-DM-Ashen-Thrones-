# PR-DE Duplicate Verification

Equality is `json.dumps(value, ensure_ascii=False, sort_keys=True)`. Byte sizes below are `json.dumps(value, ensure_ascii=False)` of the top-level value, which is the PR-DD object-size definition. They do not include the parent key punctuation. That punctuation is why the request shrank by more than 10,947 bytes.

Checked on every representative request before omission. All twelve fixtures had the same equality pattern.

| Top-level field | Policy child | Present | JSON-equal | S1 value bytes |
|---|---|---|---|---:|
| `anti_railroading_contract` | `response_policy.anti_railroading` | yes | yes | 1,451 |
| `context_separation_contract` | `response_policy.context_separation` | yes | yes | 3,801 |
| `player_facing_narration_purity_contract` | `response_policy.player_facing_narration_purity` | yes | yes | 373 |
| `social_response_structure_contract` | `response_policy.social_response_structure` | yes | yes | 625 |
| `interaction_continuity_contract` | `response_policy.interaction_continuity` | yes | yes | 2,179 |
| `fallback_behavior` | `response_policy.fallback_behavior` | yes | yes | 1,526 |
| `conversational_memory_window` | `response_policy.conversational_memory_window` | yes | yes | 992 |
| `interaction_continuity` | `response_policy.interaction_continuity` | yes | no | 261 |

S1 equal-value sum: 10,947 bytes. No fixture had a differing value for those seven mappings, so none of those fields was retained. The 261-byte snapshot was retained on every fixture.

After the change, each serialized request has `exact_duplicate_bytes` 0, and restoring the seven fields from the surviving policy children reproduces the baseline payload.
