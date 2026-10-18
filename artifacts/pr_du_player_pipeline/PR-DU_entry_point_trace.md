PR-DU Entry Point Trace

Production path:
static/app.js sendChat -> POST /api/chat -> game.api.api_chat -> game.api.chat -> intent/routing -> _resolve_engine_noncombat_seam -> existing exploration/social resolvers -> _run_resolved_turn_pipeline -> _apply_authoritative_resolution_state_mutation -> _build_gpt_narration_from_authoritative_state or deterministic OOC response -> _complete_opening_turn_persistence_like_chat -> append_log/_build_turn_response_payload.

Experimental path:
experiments/pr_dr/turn.py and experiments/pr_dq/gameplay.py replay stored interpretations against DisposableHarness. PR-DU does not invoke that dispatcher from the production turn.

Shared components:
Existing game.exploration.resolve_exploration_action, game.social.resolve_social_action, scene graph validation, storage persistence, final emission, and session log packaging.

New production bridge:
game.player_interpretation_bridge.normalized_action_from_interpretation validates a stored interpretation against current visible scene/world entities and returns the same normalized action shapes already consumed by the production chat path.
