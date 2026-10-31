# 01 — Baseline and Failure Reproduction

## Repository baseline

- HEAD: `b012c3d` — `fix: create pytest temp parent on clean CI checkouts`.
- The preexisting dirty worktree was preserved. This pass did not commit or push.
- Production change is confined to `game/api.py` (+272 / −18 against the worktree base for the three tracked files). New test: `tests/test_pr_play_04_opening_integrity.py`.
- Orientation read before the edit: `docs/DEVELOPMENT_CONSTITUTION.md`, `docs/NEXT_SESSION.md`, `docs/validation_evidence_standard.md`, `docs/product_realization_validation.md`.
- Historical owner: PR-PLAY-03 reports under `development/campaigns/product_realization/pr_play_03/` and `artifacts/pr_play_03/`. Manual capture `artifacts/pr_play_02/manual-20261026-201939.zip` remains the live trace. Its raw provider body was not retained. This pass did not try to reconstruct it.

## Historical evidence

PR-PLAY-03 recorded one metered opening. The structured contract rejected it as `missing_structured_envelope`. The player then saw “No one here can answer that from what is settled here.” Provenance was `safe_nonresolution`. The campaign was marked started and turn, time pressure, and faction progression were committed. A separate pipeline exception rolled the turn counter back and left the pressure and faction tick on disk.

## Pre-change reproduction

Command, offline, socket denied, SDK stubbed:

`python artifacts/pr_play_04/pre_change_reproduce.py`

Evidence: `artifacts/pr_play_04/pre_change/`.

Functions exercised: `api.new_campaign`, `api.start_campaign`, `api._run_resolved_turn_pipeline`, `api._build_gpt_narration_from_authoritative_state`, `api._complete_opening_turn_persistence_like_chat`, `world.advance_world_tick`, `gm.call_gpt`.

Initial state for every case: `campaign_started` false, turn 0, `time_pressure` 0, empty log, `frontier_gate`, factions house_verevin 2/0, ash_cowl 2/0, ordo_pyric 1/0, no faction events. `campaign_can_start` true.

| Case | Provider control | Contract / disposition | Player text | Final state |
| --- | --- | --- | --- | --- |
| valid_structured | JSON envelope, `declared_claims: []`, seed-restating narration | HTTP 200, provenance `initial_generation` | Exact narration | started, turn 1, pressure 1, factions 3/3/2, agendas 1, two `faction_pressure` events, 1 SDK call |
| missing_envelope | Plain prose “You stand beside the gate in the rain.” | HTTP 200, reason `missing_structured_envelope`, provenance `safe_nonresolution` | “No one here can answer that from what is settled here.” | started, turn 1, pressure 1, factions 3/3/2, agendas 1, two faction events, 1 SDK call |
| pipeline_exception | Pipeline raises before dispatch | `RuntimeError: synthetic pipeline failure` | none | started false, turn 0, log 0, but pressure 1 and factions already 3/3/2 with two events, 0 SDK calls |

The original host failure is reproducible. Implementation was allowed to proceed.

## Confirmed mechanisms

1. A rejected `scene_opening` reaches the narration catch-all for operation `unresolved` with no interlocutor. `run_preserve_if_valid` seals `safe_nonresolution`. Completion then treats that seal as a successful opening.
2. `start_campaign` increments the turn, runs `advance_world_tick`, and `save_world` before the opening is accepted. The exception handler rolls back the turn counter and session only. Pressure and faction writes remain.

## Scope confirmation

In scope: opening acceptance at the existing completion boundary, and opening-only commit integrity.

Out of scope and not reopened: ATGB-R1 conversational correction, ATGB-R2 speech grounding, ATGB-R2 question-to-evidence, PR-PLAY-02 admission and retry controls, prompts, schemas, models, output-token limits, and ordinary information-request behavior.
