# Regression Results

Milestone: `pr_play_grounded_unresolved_action_handling`. Generated 2026-11-10T07:20:54.470188-05:00. All source paths are repository-relative. Evidence root: `artifacts/pr_play_grounded_unresolved_action_handling/`. Verdict: **B/PARTIAL**.

Exact selections/options/executables are recorded in *_command.txt, with output and JUnit. Combined before: 405 passed / 20 failed / 0 errors / 0 skipped. Combined final: 403 passed / 22 failed / 0 errors / 0 skipped. Focused owner selection: 611 passed / 0 failed / 0 errors / 0 skipped (includes all 37 marking lifecycle tests). New verified tests: 8 passed / 0 failed / 0 errors / 0 skipped. Supplemental final orchestration/retreat selection: 33 passed / 1 failed / 0 errors / 0 skipped. Full suite not run.

New combined failure identities:

- `tests.test_at_opt_02_retreat_and_budget::test_f3_retreat_is_not_primary_narration_when_physical_is_disabled`
- `tests.test_pr_play_post_npc_handoff::test_genuine_travel_still_changes_scene`

The two new failures require either the exact previous generic retreat sentence or its old unsupported wording. The tests also concern no primary narration, no tick/mutation/provider, and publication classification; dedicated contextual HTTP checks verify those behaviors. These are intentional text-contract incompatibilities, not silently excluded or fixed by editing expectations. The earlier 20 identities are preserved in BASELINE and machine-readable regression_results.json with failure messages/details. Newly passing identities: `[]`.

Intermediate runs are retained, including initial new-test setup failures and the acceptance acknowledgment failure. Narrow route/ambiguity edits were made while the first focused run was active; the final source delta is covered by final supplemental/new controls, and the final combined run starts after production edits. The 611 run is therefore reported with that provenance limitation, not represented as a fresh independently captured pre-edit focused baseline.

Original twelve: only T12 text changes. T06 remains unchanged; notice contact/inspection, clue recall, travel and the marking lifecycle preserve their successful outputs. See twelve_turn_comparison.json and valid_action_controls.json.
