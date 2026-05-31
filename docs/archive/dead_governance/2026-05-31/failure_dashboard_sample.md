# Failure Dashboard Sample

Generated from controlled classifier probes shaped like existing golden replay observation rows.  The artifact demonstrates one row per replay-local failure classification without reading or mutating runtime systems.

| Scenario | Turn | Category | Severity | Primary Owner | Secondary Owner | Investigate First | Replay Tags | Unavailable | Final Source | Fallback | Mutation Flags | Field |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|
| directed_npc_question_probe | 0 | speaker | critical | speaker | emission | game/speaker_contract_enforcement.py | speaker_mismatch, structural_drift | none | generated_candidate | none | none | selected_speaker_id |
| fallback_probe | 1 | fallback | high | fallback | emission | game/final_emission_gate.py | fallback_source_mismatch, structural_drift | none | global_scene_fallback | gate_terminal_repair | none | final_emitted_source |
| route_metadata_probe | 3 | route | medium | route | projection | game/interaction_context.py | missing_observation, missing_route_metadata, structural_drift | route_kind | generated_candidate | none | none | route_kind |
| sanitizer_probe | 2 | sanitizer | critical | sanitizer | emission | game/output_sanitizer.py | scaffold_leakage, semantic_drift | none | generated_candidate | none | scaffold_leakage | scaffold_leakage |
| semantic_mutation_probe | 4 | semantic_mutation | critical | semantic_mutation | emission | game/stage_diff_telemetry.py | semantic_drift, semantic_mutation | none | generated_candidate | none | semantic_mutation | final_text |
