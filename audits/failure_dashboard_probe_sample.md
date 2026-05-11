# Failure Dashboard Probe Sample

- Generated at: `2026-05-11T00:00:00Z`
- Command: `python -m pytest -m failure_dashboard_probe -q`

| Scenario | Turn | Category | Severity | Primary Owner | Secondary Owner | Investigate First | Evidence | Replay Tags | Field | Expected | Actual | Unavailable | Final Source | Fallback | Post-Gate Mutation | Mutation Flags |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| forced_fallback_source | 1 | fallback | high | fallback | emission | game/final_emission_gate.py | sublayer=terminal_fallback; mutation=terminal_fallback | fallback_source_mismatch, structural_drift | final_emitted_source | generated_candidate | global_scene_fallback | none | global_scene_fallback | gate_terminal_repair | False | none |
| missing_route_metadata_raw_absent | 4 | route | medium | route | projection | game/interaction_context.py | missing=runtime_missing_raw_absent | missing_observation, missing_route_metadata, structural_drift | route_kind | present | none | route_kind | generated_candidate | none | False | none |
| missing_route_metadata_raw_present | 5 | projection | medium | projection | none | tests/helpers/golden_replay.py | missing=projection_missing_raw_present | missing_observation, structural_drift | route_kind | present | none | route_kind | generated_candidate | none | False | none |
| post_gate_unknown_mutation | 7 | emission | high | emission | validator | game/final_emission_gate.py | sublayer=emission.post_gate_mutation_unknown; mutation=emission.post_gate_mutation_unknown | structural_drift | post_gate_mutation_detected | False | True | none | generated_candidate | none | True | none |
| response_type_repair_unexpected | 3 | emission | medium | emission | validator | game/final_emission_gate.py | sublayer=response_type; repair=thin_answer; mutation=response_type | response_type_repair_mismatch, structural_drift | response_type_repair_used | False | True | none | generated_candidate | none | False | response_type_repair_mismatch |
| sanitizer_leakage | 2 | sanitizer | critical | sanitizer | emission | game/output_sanitizer.py | sublayer=sanitizer; mutation=sanitizer; sanitizer_mode=strip_only; sanitizer_events=1; sanitizer_changed=0 | scaffold_leakage, semantic_drift | scaffold_leakage | False | True | none | generated_candidate | none | False | scaffold_leakage |
| semantic_mutation | 6 | semantic_mutation | critical | semantic_mutation | emission | game/stage_diff_telemetry.py | none | semantic_drift, semantic_mutation | final_text | include 'east-road talk' | The answer changed. | none | generated_candidate | none | False | semantic_mutation |
| wrong_speaker | 0 | speaker | critical | speaker | emission | game/speaker_contract_enforcement.py | none | speaker_mismatch, structural_drift | selected_speaker_id | runner | guard | none | generated_candidate | none | False | none |
