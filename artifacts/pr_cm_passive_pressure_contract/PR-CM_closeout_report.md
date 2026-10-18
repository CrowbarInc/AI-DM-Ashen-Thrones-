# PR-CM closeout report

MODE: PASSIVE-PRESSURE TEST CONTRACT CLOSEOUT

LIVE CALLS: 0

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

The worktree was already dirty with earlier uncommitted product work. That work was left in place. No product file was edited. No repository reset was performed.

## Decision

A — PASSIVE-PRESSURE CONTRACT CLOSED

Both revised tests pass. They check session `time_pressure`, `advance_world_tick` results, the hard-valid seal, scene-momentum due state, and a grounded stall. They do not require the deleted interruption templates.

Grounded-observation protections are unchanged. The two follow-up failures in that file are the ones PR-CL already recorded.

The shared pipeline moved from 39 passed / 26 failed to 41 passed / 24 failed. The only names that left the failure list are the two obsolete tests. No new shared-pipeline failure appeared.

## What changed

- Replaced `test_chat_single_wait_in_tense_scene_forces_interaction_pressure` with `test_chat_single_wait_records_world_progress_and_keeps_hard_valid_narration`.
- Replaced `test_chat_repeated_passive_actions_do_not_stall_into_atmosphere` with `test_chat_repeated_passive_waits_advance_world_and_ground_scene_stall`.
- Removed `_assert_concrete_pressure`.
- Added deterministic controls A–D and a separate lead-subject diagnostic in `tests/test_pr_cm_passive_pressure_contract.py`.

## What was not changed

Invented interruption templates were not restored. No world-time mechanic was added. Narration validators were not weakened. The malformed `as you` lead was not repaired.

## Secondary finding

The scene-stall sentence can be stored as `visible_suspicious_figure.subject = "as you"`. The extractor is `_extract_visible_figure_candidate`. The record is durable, it is fed to the next provider payload, and the pressure picker will select it. It does not create an NPC or rewrite scene facts. Repair belongs in a separate extractor cycle.

## Recommended next step

Leave the remaining 24 shared-pipeline failures in their existing clusters.

If the lead parse is repaired, bound that work to `_extract_visible_figure_candidate` so `As you watch the scene` is not the figure subject. Do not use that repair to bring back approach templates.
