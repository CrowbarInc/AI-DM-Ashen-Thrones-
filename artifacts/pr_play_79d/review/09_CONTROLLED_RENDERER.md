# Controlled-renderer regression

Original test: tests.test_pr_play_47_controlled_renderer::test_matrix[5]. Input: I examine the rubbing. The test constructs a known-outcome resolution with previously visible mason-mark text, previews three controlled rendering plans, and invokes deterministic narration selection. Starting state and expected payload are the unchanged row snapshot.

The unexpected payload consisted of publication-contract metadata added by narration_skip during its repeat fast path, not a new discovery, renderer state write or provider proposal. Reproduction: renderer_before.xml. Repair: no mutation in the repeat selector. Original row == original and all authority/hidden-exclusion assertions pass unchanged in final_source_development.xml and full historical regression. The offline renderer remains outside gameplay wiring.

The original standalone unexpected payload was not separately captured; its failed equality/diff is retained in renderer_before.xml. Final actual before/after payloads and the three controlled outputs are captured in controlled_renderer_payloads.json.
