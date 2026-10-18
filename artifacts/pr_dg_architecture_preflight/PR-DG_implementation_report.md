# PR-DG Implementation Report

MODE: ARCHITECTURAL EXPERIMENT PREFLIGHT

LIVE PROVIDER CALLS: 0

PR-DF inherited decision: A — COMPARISON READY

PR-DG decision: A — PREFLIGHT READY

Scripted A, B, and C stay inside the shared authority contract on the scored rows, the adversarial controls do not commit, and scenarios 1–9 match on the mechanical tuple.

Scripted plans and scripted tool transcripts are not evidence that a live planner or a live tool-using model would choose those steps.

## Phase 0 — worktree

| Item | Value |
|---|---|
| HEAD | `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` |
| HEAD subject | PR-BN bounded DM improvisational authority |
| Worktree | Dirty before this cycle. Left dirty. Production saves were already modified and were not reset. |
| Production saves | `data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`, plus character, campaign, and conditions, were fingerprinted. The write guard intercepted a probe to session, world, and the session log, then the scenario run recorded 0 further blocked writes. The fingerprint matched at exit. |
| Provider calls | 0. `game.gm.call_gpt` and `semantic_interpreter._invoke_interpretation_model` raise if invoked. `ASHEN_DISABLE_LIVE_INTERPRETATION=1`. |

## What was implemented

An isolated package, `experiments/pr_dg/`, plus `tests/test_pr_dg_architecture_preflight.py`. It is not imported by `chat`.

- Copied fixture bundles from the PR-DE constructors (`_gate_session_scene`, the K1 synthetic scene, `_scene_with_goblin`).
- One shared tick per turn: `advance_world_tick` then `advance_clock(session, "time_pressure", 1)`, then the turn counter increments. A second call returns `already_applied`.
- Candidate A runs `select_ordinary_resolver` on a discarded copy with interpretation pinned off, then the existing social, noncombat, exploration, or combat resolver.
- Candidate B validates a hand-authored plan and executes permitted steps through that same dispatch.
- Candidate C dispatches the eight PR-DF tools. Read-only tools are hash-checked. Writes go through the same dispatch or the same tick.
- State tuples and sha256 hashes are stored in `results.json` and `PR-DG_scenario_comparison.csv`.

## Contradictions in the PR-DF packet

These were not resolved by widening the experiment.

1. `PR-DF_experiment_design.md` says to call the PR-DE builders and the resolvers, not `chat`. `PR-DF_current_architecture_map.md` says the production path is `chat`, which loads and saves the production documents. The harness follows the experiment design. It does not call `chat`.
2. PR-DE's `_social` / `_explore` attach the contract after resolution. The architecture map builds the contract first. The harness selects the contract on a discarded copy, then calls the existing resolver. On scenarios 1–9 the selector and the executed resolver agreed.
3. Candidate B's operation enum includes `advance_time`. `semantic_interpreter._ALLOWED_OPERATIONS` includes `unresolved` and does not include `advance_time`. The harness uses the B enum for plans. It does not treat `advance_time` as a second clock.
4. `call_gpt` invokes `responses.create(model=route.selected_model, input=messages)` with no temperature and no max-token keyword. Interpretation uses temperature 0 and `max_output_tokens` 400. Those are the code values. Narration temperature was not invented. Recorded model name: `gpt-4.1-mini`.
5. `build_canonical_referent_catalog` does not list scene enemies. `resolve_attack` addresses enemies on the scene document. The validator accepts an id that is already an enemy on that scene and records the gap. It does not mint enemies.
6. `_apply_authoritative_resolution_state_mutation` raises if the scene is marked `_is_canon`. `load_scene` sets that flag. The harness uses `build_effective_scene`, the existing gameplay copy, and does not write canon files.

## Scenario outcome

| # | Id | A status | A resolver | B status | B transaction | C status | C rounds | Match 1–9 | Sheet |
|---|---|---|---|---|---|---|---|---|---|
| 1 | S1 | completed | social | completed | atomic_per_resolver_call | completed | 3 | True | A:True,B:True,C:True |
| 2 | S2 | completed | social | completed | atomic_per_resolver_call | completed | 3 | True | A:True,B:True,C:True |
| 3 | F1 | completed | social | completed | atomic_per_resolver_call | completed | 3 | True | A:True,B:True,C:True |
| 4 | H1 | completed | social | completed | atomic_per_resolver_call | completed | 3 | True | A:True,B:True,C:True |
| 5 | M1 | completed | travel | completed | atomic_per_resolver_call | completed | 3 | True | A:True,B:True,C:True |
| 6 | O1 | completed | exploration | completed | atomic_per_resolver_call | completed | 3 | True | A:True,B:True,C:True |
| 7 | K1 | completed | exploration | completed | atomic_per_resolver_call | completed | 3 | True | A:True,B:True,C:True |
| 8 | B1 | completed | combat | completed | atomic_per_resolver_call | completed | 3 | True | A:True,B:True,C:True |
| 9 | C1 | completed | social | completed | atomic_per_resolver_call | completed | 3 | True | A:True,B:True,C:True |
| 10 | compound | completed | travel | partial | partially_committed | partial | 4 |  | A:True,B:True,C:True |
| 11 | ambiguous | completed | social | completed | rejected_before_execution | completed | 3 |  | A:True,B:True,C:True |
| 12 | courier | completed | social | completed | atomic_per_resolver_call | completed | 3 |  | A:True,B:True,C:True |
| 13 | declared_canon | completed | world_action | completed | rejected_before_execution | completed | 3 |  | A:True,B:True,C:True |
| 14 | mechanical_dump | completed | social | completed | rejected_before_execution | completed | 3 |  | A:True,B:True,C:True |

Scenarios 1–9 match on scene id, clue ids, enemy HP, interlocutor, time pressure, and tick event types. Illegal plans and illegal tool transcripts on scenarios 10, 13, and 14 do not commit HP, flags, or hidden strings.

Scenario 12 moved `df_mobile_courier` to `market_quarter` with one `npc_moved` event for A, B, and C. That is the current tick, not an engine gap.

## Decision

**A — PREFLIGHT READY.**

The three scripted interfaces run through the existing resolvers under one authority contract. The adversarial controls do not commit unauthorized changes. A bounded live comparison can use the PR-DF minimum set. It still has to pin interpretation off for A, inject the combat die, keep isolated copies, and treat planner or tool quality as unmeasured.

Recommended next step: a bounded live arm on S1, the compound pry, the ambiguous ask, the declared-canon line, C1, and B1. No production saves. No claim that this preflight measured narrative quality.
