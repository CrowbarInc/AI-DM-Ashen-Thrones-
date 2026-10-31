# 06 — Regression and Performance

## Focused opening matrix

`python -m pytest tests/test_pr_play_04_opening_integrity.py -q --tb=line`

18 passed, 0 failed, exit 0.

## Broader non-HTTP slice

`tests/test_pr_play_02_controls.py`, `tests/test_provider_accounting_integrity.py`, three immutable-boundary cases (`test_case_b_double_invalid_emits_safe_nonresolution_and_stops`, `test_safe_nonresolution_does_not_invent_or_quote`, `test_case_c_valid_initial_does_not_retry`), two opening-fallback cases (`test_valid_scene_opening_skips_deterministic_fallback`, `test_failed_scene_opening_never_emits_generic_the_scene_fallback`), and two scene-canon cases.

95 passed, 1 failed, exit 1. About 20 seconds.

### Preexisting failure

`tests/test_provider_accounting_integrity.py::test_readiness_acceptance_is_not_live_execution`

`live_accounting_readiness` fails closed because the reviewed application fingerprint does not match this worktree. Gaps:

- `reviewed_application_surface_changed`
- `accounting_implementation_changed` (`game/provider_budget.py` hash)
- guarded-but-changed dispatch owners in `game/gm.py:call_gpt`, `game/expressive_dialogue.py:request_expression`, `game/host_constrained_candidates.py:invoke_candidate_provider`, `game/live_chat_interpretation.py:request_interpretation`, `game/semantic_interpreter.py:_invoke_interpretation_model`, `game/unified_semantic_planning.py:_invoke_provider`

Those dispatch sites remain wrapped in `attempt.dispatch`. This pass did not add a provider call site and did not edit `provider_budget.py`. The frozen manifest was not updated. Classification: preexisting fingerprint drift on the dirty tree, plus this pass’s `game/api.py` edit as one more surface-hash difference. Not repaired.

## HTTP slice

`tests/test_start_campaign_api.py`, `tests/test_opening_start_seam_regressions.py`, and `tests/test_scene_canon_hygiene.py::test_campaign_start_and_playthrough_do_not_modify_scene_files`, with a 50 second cap.

The run finished well inside the cap. The historical TestClient hang did not reproduce. Output: `artifacts/pr_play_04/regression_http_out.txt`.

23 tests: 18 passed, 5 failed.

Passed includes the opening seam file (prompt basis, chat begin, contaminated opening, failed start leaves turn and log clean, start-then-chat) and the scene-file immutability test. Also passed: fresh compose flags, empty new-campaign log, log has no synthetic player line, second start rejected, prompt contract fields, UI bootstrap copy, and failed start does not mark the campaign started.

### New, intended contract outcomes

- `test_start_campaign_frontier_gate_uses_journal_seed_facts_when_opening_seed_absent`
- `test_start_campaign_opening_fallback_basis_uses_journal_seed_not_visible_facts`

Both stub `call_gpt` with `FAKE_GPT_RESPONSE` (`player_facing_text` `"[Narration]"`). The opening is now HTTP 422 `opening_failed`, reason class `scene_opening_not_scene_establishing`. A direct probe showed the sealed text still `"[Narration]"` with provenance `initial_generation`. The journal sentence was not substituted. These tests expected HTTP 200. The placeholder is not a valid opening, so the contract was not weakened to restore the old status. Classification: new status result of this repair. The missing journal sentence in the sealed text is the preexisting seal, not a new substitution bug.

### Indeterminate rich-text length failures

- `test_start_campaign_emits_opening_and_sets_started`
- `test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text`
- `test_start_campaign_promotes_valid_upstream_prepared_scene_opening`

Each returned HTTP 200. The new completion guard therefore accepted the text. The failing assertions are that the player text is a substring of the rich stub and that `post_final_emission_gate_text_len` is greater than 800. The observed gate length is 781. These stubs are dicts without `structured_contract_failure`, so the new catch-all skip does not apply. The length is produced by the emission gate this pass did not edit. They were not bisected against a clean HEAD because the worktree was already dirty. Classification: indeterminate, treated as preexisting emission-path drift until a clean bisect says otherwise. Not repaired here.

## Local overhead

One successful stubbed opening, including process start and `new_campaign`, measured 1.60 seconds wall clock (`Measure-Command` around `pre_change_reproduce.py valid_structured` after the repair). The added host work is a deepcopy of session, world, and combat, plus holding the existing persistence lock for the attempt. No token-use or provider-latency claim.

## Incomplete coverage

The full suite was not run. No browser pass was required; the UI was not redesigned. No live provider call was made.
