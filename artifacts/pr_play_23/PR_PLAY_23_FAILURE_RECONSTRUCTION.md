# PR-PLAY-23 failure reconstruction

Original request: “I approach the tavern runner and ask what they're offering.”

The captured provider envelope describes MOVE(tavern_runner), then ASK(tavern_runner), orders 1/2. Its communication is NPC/QUESTION; interpretation status INTERPRETED; no unresolved references. The provider was asked to describe ordered attempts using MOVE and ASK, not to authorize them. Separating physical approach from speech was reasonable.

Evidence: artifacts/atgb/pr_play_22/live/turns/T1/{api_response.json,parser_validation_diagnostics.json,before/persistent/}; artifacts/pr_play_22/PR_PLAY_22_FAILURE_ANALYSIS.md. A minimal captured envelope and parsed record are copied into captured_interpretation_fixture.json.

Call path: api._chat_turn → live_chat_interpretation.interpret_production_turn → contract adaptation. Parsing succeeds and disposition is ELIGIBLE_FOR_VALIDATION. The live adapter returns blocked/clarification_required because it has two components; this is a recoverable handoff to compound orchestration, not the decisive refusal. api._chat_turn invokes conversational_orchestration.decision_from_interpretation_record → _compound_from_record_parts → _compound_clarification. Each proposed step goes through player_interpretation_bridge.normalized_action_from_interpretation. MOVE expects catalog kind exit; tavern_runner has kind npc. The bridge returns operation_incompatible_with_entity_kind. ASK binds successfully. _compound_clarification sees unsupported first step and returns proposal_not_eligible. No resolver or narration invocation occurs.

First decisive failed boundary: engine MOVE binding, not interpretation, parser, NPC registration, dialogue transport, or NPC knowledge disclosure. Compound orchestration then correctly preserves sequence safety under its old all-consequential interpretation.

Published refusal: “I cannot carry out Approach the tavern runner, then Ask the tavern runner what they are offering with the available actions and targets. I have not done any of them yet.”

Offline reproduction: test_original_failure_boundary uses the actual captured scene/world and parsed record through the unchanged production bridge and orchestrator, disabling only the new normalization. It reproduces the kind mismatch and original refusal with no input mutation (original_reproduction.json). The successful integration replays the ORIGINAL RAW provider envelope through the real request builder/parser, orchestration, resolver and Player HTTP publication. It does not replay engine-enriched parsed fields as provider JSON.

Authority distinction: interpretation proposes; parsed records preserve unadjudicated premises/outcomes; bridge checks kinds and grounding; resolver owns authorization and effects; response publication uses existing validated host/NPC speech. Successful normalization grants no movement authorization.
