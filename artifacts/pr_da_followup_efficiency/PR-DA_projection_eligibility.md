# PR-DA Projection Eligibility

Predicates are the PR-CW conditions in `game.gm._project_harmless_social_provider_context`, evaluated in source order on the pre-projection payload of the reconstructed follow-up.

Reduced context was not forced.

First failing predicate: `exactly_one_allowed_speaker`.

The follow-up is genuinely ineligible for reduced context. `speaker_selection.allowed_speaker_ids` is empty, and the projector requires exactly one grounded speaker. That predicate is doing the safety job it was written to do. The upstream speaker selector reported `no addressable target resolved` even though `resolution_contract.interlocutor` is `guard_captain`. The predicate was not modified and eligibility was not forced.

Response envelope: `narration_only`.

Projector selection on the captured request: not selected. The provider payload has no `provider_context_projection` field.

## Measurements

Full-context serialized bytes are measured from the pre-projection payload plus the system prompt captured for this follow-up.

- Full-context serialized bytes: 127336
- Full-context estimated tokens (bytes/4): 31834
- Hypothetical reduced-context serialized bytes: 114058
- Hypothetical reduced-context estimated tokens (bytes/4): 28514

Hypothetical bytes apply the omission steps on a copy. They are not live savings and were not sent.

Retained history entries: 3.

```json
[
  {
    "player_input": "Guard Captain, do you prefer standing watch in the rain, or somewhere dry?",
    "gm_snippet": "The guard captain shrugs slightly, water dripping from the brim of their helmet as rain spatters the soot-dark stone of Cinderwatch's eastern gate. \"I suppose most would prefer dry ground,\" they say w"
  },
  {
    "player_input": "",
    "gm_snippet": "guard captain shrugs slightly, water dripping from the brim of their helmet as rain spatters the soot-dark stone of cinderwatch's eastern gate [active_event_guard_captain_shrugs_slightly_water_drippin"
  },
  {
    "player_input": "",
    "gm_snippet": "keeps you sharp, or maybe just miserable enough to stay alert.\" their gaze flickers briefly to the frayed banners hanging overhead, and then back to the queue clogged with refugees and wagons [active_"
  }
]
```

| Predicate | Required | Actual | Result | Authority source |
|---|---|---|---|---|
| `payload_is_dict` | `dict` | `dict` | PASS | `projector payload argument` |
| `provider_response_contract` | `narration_only` | `narration_only` | PASS | `build_messages selected envelope passed into the projector` |
| `recipe_is_dict` | `True` | `True` | PASS | `payload.decision_facing_answer_recipe` |
| `turn_operation_is_dict` | `True` | `True` | PASS | `payload.decision_facing_answer_recipe.turn_operation` |
| `response_operation` | `incidental_dialogue` | `incidental_dialogue` | PASS | `turn_operation.response_operation` |
| `declaration_expectation` | `reply_not_required` | `reply_not_required` | PASS | `turn_operation.declaration_expectation` |
| `decision_is_dict` | `True` | `True` | PASS | `payload.gm_resolution_decision` |
| `permitted_state_mutations` | `[]` | `[]` | PASS | `gm_resolution_decision.permitted_state_mutations` |
| `unresolved_qualifiers` | `[]` | `[]` | PASS | `gm_resolution_decision.unresolved_qualifiers` |
| `unresolved_content_absent` | `True` | `True` | PASS | `decision_facing_answer_recipe.unresolved_content` |
| `permitted_inference_is_dict` | `True` | `True` | PASS | `decision_facing_answer_recipe.permitted_inference` |
| `permitted_inference_allowed` | `False` | `False` | PASS | `permitted_inference.allowed` |
| `contract_is_dict` | `True` | `True` | PASS | `payload.resolution_contract` |
| `contract_operation` | `ask` | `ask` | PASS | `resolution_contract.operation` |
| `contract_target_nonempty` | `True` | `True` | PASS | `resolution_contract.target` |
| `response_policy_is_dict` | `True` | `True` | PASS | `payload.response_policy` |
| `scene_is_dict` | `True` | `True` | PASS | `payload.scene` |
| `dialogue_plan_is_dict` | `True` | `True` | PASS | `payload.dialogue_social_plan` |
| `speaker_selection_is_dict` | `True` | `True` | PASS | `payload.speaker_selection` |
| `allowed_speaker_ids_is_list` | `True` | `True` | PASS | `speaker_selection.allowed_speaker_ids` |
| `exactly_one_allowed_speaker` | `1` | `0` | FAIL | `speaker_selection.allowed_speaker_ids length` |
