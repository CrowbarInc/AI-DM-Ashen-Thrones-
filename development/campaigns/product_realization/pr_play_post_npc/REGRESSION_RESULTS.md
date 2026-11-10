# Regression results

Live provider calls: 0. Pytest processes were not run in parallel after an earlier collision on `development/tmp/pytest`.

## New tests

`tests/test_pr_play_post_npc_handoff.py`

Command:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_pr_play_post_npc_handoff.py -q
```

Result: 7 passed. The tests post `/api/chat` with provider calls disabled and the production `call_gpt` restored, which returns before the network.

Covered: the captain-then-approach-read-copy-recall sequence; three explicit repeats; a return to the captain; genuine travel and the unsupported retreat; unknown destination; unknown object; hidden content; an ambiguous two-object question.

## Existing adjacent tests

A sequential run of conversational continuity, referenced-surface grounding, action admission, AT-OPT-02, AT-OPT-04, AT-OPT-06, transition-node, prompt-consumption, and provider-efficiency tests reported 12 failures:

- HTTP cases in `tests/test_referenced_surface_grounding_inspection_resolution.py` from `test_general_unknown_player_named_object_is_not_instantiated` through `test_observe_stock_replacement_keeps_notice_board_working`.
- `test_sequence_patrol_travel_reaches_the_movement_resolver` and `test_sequence_unsupported_actions_invent_nothing` in `tests/test_pr_play_39_action_admission.py`.

The unit classifier `test_general_short_alias_does_not_steal_more_specific_visible_feature` passed. Isolated probes showed `deterministic_conversational_decision` returning None for the mill-loft inspect and look utterances. Player projection sets `resolution` to `{}`. A pre-edit rerun was not obtained: `git checkout HEAD` of the four production files removed `authored_travel_admission` and pytest could not collect. Those files were restored from the in-progress backup. The 12 failures are recorded, not classified as new identities, and not classified as baseline.

`test_http_fallback_is_not_an_operational_refusal` failed during a parallel collision and passed when rerun alone.

Known baseline KeyErrors reproduced in the collided publication run: `provider_context_projection`, `gm_only`, `social_context`.

## Protected tests

Redirected holdout, after the frontier-gate scene was restored:

```text
.\.venv\Scripts\python.exe artifacts\pr_play_post_npc\rerun_holdout.py
```

Result: 28 passed, 0 failed, 0 blocked non-local connections. An earlier parallel run failed `H18_continuation` and blocked 3 connections while `data/scenes/frontier_gate.json` had lost its interactables. That result is discarded. The historical file `artifacts/pr_play_79df3/holdout_results.jsonl` was not rewritten. The redirected result is `artifacts/pr_play_post_npc/holdout_rerun.json`.

Protected rehash: 150 unchanged, 0 changed, 0 missing. File: `artifacts/pr_play_post_npc/protected_rehash.json`.

## AT-OPT protections

The AT-OPT-06 tests were in the adjacent command and were not among the 12 named failures. Retreat routing, the same-scene transition, and the frozen holdout remained intact on the solo rerun: T11 still transitions, T12 still refuses, holdout 28/28.

## New failures

No new regression identity is claimed. The 12 adjacent HTTP failures remain unresolved against a pre-edit baseline.
