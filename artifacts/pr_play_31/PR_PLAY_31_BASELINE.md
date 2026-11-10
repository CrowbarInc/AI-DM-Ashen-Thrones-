# PR-PLAY-31 baseline
Revision: `d40f1ed198236c604085f1c842ead267a8104ce2`. Working tree was extensively dirty; inherited status is preserved in git_status_before.txt. No commit, reset, or push was performed.

Before editing: captured conversational_orchestration.before.py and ran the actual PR-PLAY-30 HTTP harness with all model surfaces mocked and the existing live-call guard enabled. baseline_reproduction.json preserves the complete original run.

Exact command: I head northwest of the crates to investigate the muddy footprints.

Original extracted destination: `investigate the muddy footprints`. No purpose field; `investigate` absent from the router's inspection cues. Router: MOVE -> DECLINE / destination_not_established. No selected target, interpreter call, exploration resolver, or gameplay parser invocation. No turn or clock advance, scene transition, inventory, currency, or clue mutation; social interlocutor bookkeeping cleared and refusal logged.

Published: You want to reach investigate the muddy footprints, but that is not an established destination from here. You stay where you are.

Baseline primary: 210 passed, 1 setup error, zero assertion failures, 211 collected including the historical observation harness. Comparable primary subset excludes that one observation test (which intentionally asserts the old failure): 209 passed + one setup error over 210 tests. Additional comparable suite: 75 passed, seven assertion failures over 82 tests. Baseline WinError 5 in session.json atomic replacement is preserved verbatim. An earlier inventory invocation named two nonexistent test files and collected zero tests; baseline_extra.txt records this command error. Corrected invocation completed normally; no unresolved collection error.

Entry points: game/conversational_orchestration.py (_destination_phrase, _analyze_clause, _committed_movement_or_compound_decision, _resolve_move_target, _resume_bounded_pending); game/local_interaction.py normalize_local_approach; game/player_interpretation_bridge.py normalized_action_from_interpretation; game/exploration.py resolve_exploration_action; game/clues.py apply_socially_revealed_leads and clue_knowledge; game/api.py _apply_authoritative_clues_from_resolution and _apply_authoritative_resolution_state_mutation; game/scene_graph.py is_transition_valid; tools/playtest/gameplay.py evaluate; tools/playtest/overlays.py compare_overlays. Current copies are packaged under source/.
