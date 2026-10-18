PR-DU Implementation Report

Mode: production-path integration
Live provider calls: 0
Head: d31beb7d73dd4fda0f22184a6a69b947b5f470ff

Summary:
- Added a production-safe stored-interpretation bridge at game/player_interpretation_bridge.py.
- Connected the bridge to the normal chat turn function in game/api.py, behind an injectable no-op provider hook. Normal runtime behavior is unchanged unless a replay/test harness supplies stored interpretation records.
- Added a narrow non-mutating OOC correction branch for explicit appearance/clarification interruptions before turn counters, clocks, world ticks, or resolvers run.
- Fixed a production transition persistence bug by saving the current in-memory session before activate_scene reloads it, preserving same-turn counters/clocks/runtime state across scene transition.
- Added focused PR-DU tests in tests/test_pr_du_player_pipeline.py.

Decision: A - PRODUCTION-PATH SLICE COMPLETE, with player-visible narration shortcomings recorded for the gate/notice turns.
