# 06 — Authority and State Integrity



Snapshots are taken after isolated setup, immediately before the player request, and after it. Canonical player data and all entry-hashed production/fixtures/experiments are unchanged. Fresh identities and delivered conversational memory are permitted setup metadata; they do not authorize world facts.



## L1 — PASS

Changed domains: ['log']; session keys: []; world keys: [].

Turn 0→0; clocks before {'suspicion': 0, 'unrest': 0, 'danger': 0, 'occult_instability': 0, 'time_pressure': 0}; after {'suspicion': 0, 'unrest': 0, 'danger': 0, 'occult_instability': 0, 'time_pressure': 0}.

Pending-intention fields are fully listed in normalized_results.json and raw snapshots.



## L2 — PASS

Changed domains: ['log']; session keys: []; world keys: [].

Turn 0→0; clocks before {'suspicion': 0, 'unrest': 0, 'danger': 0, 'occult_instability': 0, 'time_pressure': 0}; after {'suspicion': 0, 'unrest': 0, 'danger': 0, 'occult_instability': 0, 'time_pressure': 0}.

Pending-intention fields are fully listed in normalized_results.json and raw snapshots.



## L3 — PASS

Changed domains: ['session', 'log']; session keys: ['conversational_context', 'last_saved_at']; world keys: [].

Turn 0→0; clocks before {'suspicion': 0, 'unrest': 0, 'danger': 0, 'occult_instability': 0, 'time_pressure': 0}; after {'suspicion': 0, 'unrest': 0, 'danger': 0, 'occult_instability': 0, 'time_pressure': 0}.

Pending-intention fields are fully listed in normalized_results.json and raw snapshots.



## L4 — FAIL (invalid live-control setup)

Changed domains: ['session', 'world', 'log']; session keys: ['_runtime_canonical_ctir_stamp_v1', '_runtime_canonical_ctir_v1', '_runtime_narration_plan_bundle_stamp_v1', '_runtime_narration_plan_bundle_v1', '_runtime_progression_nodes_fingerprint_v1', 'bounded_improvisation', 'character_name', 'clocks', 'conversational_context', 'debug_traces', 'discourse_focus', 'emergent_actor_debug', 'interaction_context', 'interpretation_telemetry', 'last_action_debug', 'last_bounded_improvisation_promotion', 'last_saved_at', 'last_turn_response_policy', 'lead_registry', 'narration_temporal_provenance', 'npc_runtime', 'runtime_scene_overlays', 'scene_runtime', 'scene_state', 'turn_counter']; world keys: ['event_log', 'factions'].

Turn 0→1; clocks before {'suspicion': 0, 'unrest': 0, 'danger': 0, 'occult_instability': 0, 'time_pressure': 0}; after {'suspicion': 0, 'unrest': 0, 'danger': 0, 'occult_instability': 0, 'time_pressure': 1}.

Pending-intention fields are fully listed in normalized_results.json and raw snapshots.



L1/L2: session and gameplay domains unchanged; only failure-log entry appended. L3: gameplay domains unchanged; only delivered-memory and save timestamp change. No pending intention created or revised. Its question contains public people/location concepts and no restricted facts. L1/L2 generic fallback contains no restricted facts. Exact observed-output disclosure check passes within these narrow executions; no claim of exhaustive security testing.

L4: unexpected isolated mutation observed; pending_intention becomes null and last_executed_intention is marked executed. Pending clarification remains. World factions and event_log change; character/combat/scene template do not. This violates the intended control authority contract. It followed a disabled-interpretation fallback caused by test environment leakage, so the live control is INVALID and live authority preservation is not established. The statement “no unauthorized state mutations” cannot be confirmed for this pass. Canonical player state was not affected.

Integrity: 470 entry hashes and all 3564 predecessor-protected files match. Production code unchanged; frozen baseline unchanged; no experimental candidates merged; no commit or push.
