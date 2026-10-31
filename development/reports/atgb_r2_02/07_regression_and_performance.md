# 07 — Regression and Performance

## Tests executed

New file, isolated: `tests/test_atgb_r2_02_speech_participant_grounding.py` — 46 passed.

Relevant slice, one pytest process, 8.73s:

`test_pr_ef_r4_authorization`, `test_pr_eb_conversational_continuity`, `test_pr_br_continuation16_interaction_completion`, `test_pr_ea_conversational_orchestration`, `test_pr_br_continuation22_commitment`, `test_atgb_r1_02_revision_boundary`, `test_atgb_r1_07_correction_contract`, `test_pr_ck_ordinary_resolver_selection`, `test_pr_ef_r2_social_authority`, `test_directed_social_routing`, `test_vocative_direct_address_recovery`, `test_pr_br_continuation25_semantic_ownership`, and the new file.

Result: **351 passed, 2 failed**, 353 collected.

## Preexisting failures

Both failures also fail when `game/interaction_completion.py` and `game/ordinary_semantic_ownership.py` are restored to `b012c3d` and the same tests are run:

- `tests/test_pr_br_continuation22_commitment.py::test_raw_chat_stub_covers_commitment_and_addressee` — "I ask the guard what happened while watching his reaction." expects operation `ask` and gets an empty contract.
- `tests/test_directed_social_routing.py::test_chat_hailing_runner_with_can_you_question_routes_social` — expects resolution kind `question` and gets `conversational_clarify`.

Classification: **preexisting**. They were not repaired.

One authorization holdout, `correction_already_executed`, failed once in a batch that ran immediately after a temporary checkout of the pre-repair sources, then passed alone and passed in the later full slice. Classification: **environment-blocked** for that single run, not a product regression. The stable slice does not fail it.

## New regressions

None in the stable slice. The 46 new tests pass.

## Incomplete coverage

The full pytest suite was not run. Referent-tracking modules outside the slice above were not run. No Ashen Thrones Gameplay Benchmark was run. No live provider trial was run. Interrupted HTTP coverage from earlier campaigns was not repeated.

## Performance

No provider call, retry, prompt, or schema change. The new work is a bounded scan of the existing short address span. Token count and provider-call count for these turns stay at zero in this offline replay. A turn that used to stop at clarification can now reach the existing resolver. That was observed for both historical lines: one deterministic resolver call, no narration request, no admission. Latency of that existing call was not separately benchmarked. No persistent session key was added.
