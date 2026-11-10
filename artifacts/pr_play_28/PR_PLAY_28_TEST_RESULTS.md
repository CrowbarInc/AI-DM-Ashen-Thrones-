# PR-PLAY-28 test results

Final new tests: 44 executed, 44 passed, 0 failed, 0 errors (public_final.xml/public_final.txt). Covers A1–A12 and B1–B12 through parameterized positive/negative selector, authorization, evaluator and real HTTP scenarios. The full public HTTP response and internal persisted evidence are both evaluated; no direct-selector substitute is used for integration.

Broader focused scope: 226 executed, 208 passed, 18 failed. Counts overlap the final new suite; do not add them as unique tests. Existing PR-PLAY-25 authority tests: 38/38. Opening-overlay adversarial tests: 22/22. Clue-knowledge: 9/9. The remaining focused failures are preexisting: 16 social-lead landing, one question-relevance, one clue idempotence. Full IDs/messages are in focused_failure_comparison.json. No assertion was changed to hide a failure.

Comparable 73-file/1,603-test scope:

- PR-PLAY-27 historical: 1,490 passed / 113 failed.
- Fresh exact pre-repair baseline: {'passed': 1489, 'failure': 114, 'error': 0, 'skipped': 0}.
- Repaired existing run: {'passed': 1490, 'failure': 113, 'error': 0, 'skipped': 0}.
- Same exact IDs: True.
- Newly introduced regressions: 0.
- Resolved preexisting product failures: 0.
- Environmental IDs: 3 (details below).

The extra fresh-baseline failure versus PR-PLAY-27 is tests.test_start_campaign_api::test_start_campaign_frontier_gate_uses_journal_seed_facts_when_opening_seed_absent. It fails in unchanged game/storage.py atomic os.replace with WinError 5 on isolated temporary session.json, not in topic or evaluator logic. A changed result for this ID is environmental, not attributed to this repair. Full logs/XML retain all evidence.

Every current failure has an exact pre-repair status in test_comparison.json, including assertion messages and stack text. Address-only message differences are normalized for comparison; original strings remain intact. Relevant historical failures are **not assumed unrelated**. The social landing/idempotence failures remain directly related unresolved fixture/authority coverage: e.g. `_resolution_question_with_topic` supplies an invented runner/topic with default_world and lacks a matching owned authored source, so the preexisting source guard denies the write. The new positive fixtures supply actual NPC/topic/scene/action provenance. This pass does not weaken the guard or rewrite those historical fixtures. Other baseline social/dialogue failures remain preexisting unresolved, with no claim of causal independence.

One focused failure was outside the 1,603-ID list: `test_apply_socially_revealed_leads_twice_preserves_canonical_state` also fails with saved pre-pass functions (extra_baseline.xml/txt), because its invented resolution lacks a matching authored source. The targeted replay runs saved functions in a separate process without altering the working regression sources.

During implementation, the single metadata addition to the pinned benchmark fixture initially invalidated its manifest. This introduced 14 failed/error IDs in the first full post-run; existing_before_pin.xml/txt preserves that failure. The fix updates only world.json's manifest digest and the verifier's pinned manifest digest, with an explicit source note. File/hash verification remains mandatory. All 52 affected gameplay/harness/budget tests pass after the correction (pin_fixed.xml). An early targeted replay's controller KeyError('actions') also came from this temporary mismatch and is not classified as preexisting. Final focused/existing logs supersede the run with the missing pin update.

Live-provider request count: **0**. Pytest autouse live_model_guard denies unmocked transports; integration stubs the SDK, interpretation and expression and fails unexpected narration. `ASHEN_DISABLE_LIVE_*` flags are enabled only inside mocked tests. Provider-shaped stub records are not live requests. No models or provider settings changed.

Commands/scripts: run_baseline_complete.py runs the exact inherited test_files.json order; run_post.py runs focused_files.json then the same existing list, each with separate development/tmp/pr_play_28_* roots. Final new suite uses --basetemp=development/tmp/pr_play_28_public_final. No full-suite green claim is made. Initial interrupted baseline and failed UTF-8 patch invocation are superseded by the complete baseline and final runs; the encoding failure occurred before any production write.

Final scope accounting: 113 unchanged historical failures in the 1,603-test scope; one additional preexisting clue-idempotence failure outside that list; 114 unique unresolved failure IDs across all final scopes. One final full-run failure was transient WinError 5 on an already historically failing ID; clean targeted before/after controls recover its identical original assertion failure. Product failures resolved by this pass in the historical scope: 0. Newly introduced remaining regressions: 0. Unclassified final failure IDs: 0. The 18 focused historical failures are retained as related unresolved coverage; detailed provenance/fixture mismatch is not dismissed as unrelated. Fixture-integrity checks: 15 passed; affected gameplay/harness/budget checks after pin correction: 52 passed.

Environmental reconciliation: three IDs encountered WinError 5 during one of the full runs. In addition to the opening test, baseline test_by3_generate_repo_artifacts and post-repair test_chat_active_target_direct_command_routes_to_social_exchange had transient atomic-write failures. environment_before.xml/environment_after.xml rerun the two masked historical assertions against saved/current functions: both versions fail identically (assert False is True; expected social_probe, got conversational_clarify), without WinError. These remain preexisting failures with environmental overlap. The main raw full-run counts remain unchanged; no targeted result is substituted into the raw XML. test_comparison.json retains all stages. No unclassified failures or new regression IDs remain.
