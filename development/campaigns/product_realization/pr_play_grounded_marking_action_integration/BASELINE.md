# Baseline

Recorded before this cycle's edits. Branch `feature/product-realization`. HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`. The dirty worktree was left in place. No reset, clean, stash, revert, checkout, commit, or push.

Entry production SHA-256 is in `artifacts/pr_play_grounded_marking_action_integration/entry_production_hashes.txt`. After this cycle, among those files, only `game/api.py` changed. `game/marking_action.py` is new. `game/conversational_orchestration.py` and `game/intent_parser.py` differ from HEAD and match the entry snapshot, so this cycle did not edit them. Object marking, identity, observation, storage, and projection hashes match the entry snapshot.

Measured before this cycle's production edit took effect:

- Combined selection: 425 tests, 17 failed, 0 errors, 0 skipped (408 passed). Junit: `before_combined_junit.xml`.
- Focused predecessor selection: 574 tests, 1 failed, 0 errors, 0 skipped. The single failure was `tests.test_pr_play_71_persistence_recovery::test_atomic_replace_transient_lock[1]` while another pytest process was writing under `development/tmp`. It is an environmental lock-scan collision, not a product assertion about marking.
- Disclosure selection: 240 tests, 2 failed, 0 errors, 0 skipped. Failures: `test_successful_start_serialized_boundary` and `test_rejected_turn_with_composed_state` (`KeyError: character_secret`).

The original twelve-turn sequence was not re-executed before the edit. The predecessor comparison remains the before reference: T06 and T12 both published `That part is not supported here. It was not carried out.`

Historical combined reference 405 passed / 20 failed was not the measured entry result. Three classification tests that belong to that historical 20 already passed in this cycle's before run.
