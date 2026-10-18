# PR-DF Architecture Report

MODE: INTERACTION ARCHITECTURE COMPARISON AND EXPERIMENT DESIGN

IMPLEMENTATION: NONE

LIVE PROVIDER CALLS: 0

PR-DE inherited decision: A — EXACT DEDUPLICATION VERIFIED

PR-DF decision: A — COMPARISON READY

No winner is selected. Candidates B and C are specified. They are not measured.

## Phase 0 — worktree

| Item | Value |
|---|---|
| HEAD | `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` |
| HEAD subject | PR-BN bounded DM improvisational authority |
| Worktree | Dirty before this cycle. Left dirty. |
| This cycle | New files under `artifacts/pr_df_architecture_comparison/` plus the handoff review refresh. |
| Production saves | `data/session.json`, `data/world.json`, `data/combat.json`, and `data/session_log.jsonl` were already modified. This cycle did not open them for write. |
| Provider calls | 0 |

Relevant pre-existing modifications include the Product Realization game modules (`game/api.py`, `game/gm.py`, `game/prompt_context.py`, and the social, resolution, and emission modules) and the PR-DE affordability artifacts. Those files are the architecture under study. They were not edited here.

## What was compared

Three ways to turn a player utterance into an authoritative result and a narration:

- **A. Current deterministic pipeline.** Code classifies the utterance, selects one resolver, mutates state, then asks the provider to narrate the result.
- **B. AI planner + deterministic executor.** A model proposes a structured plan. The same resolvers validate and execute permitted steps.
- **C. Tool-using AI + authoritative engine.** A model calls bounded tools. Read tools return projections. Write tools call the same resolvers.

All three are required to share one world: the existing session, world, scene, combat, clocks, and ledgers. B and C do not get a second simulation.

## Evidence used

- Turn stages in `game/api_turn_support.py` (`AUTHORITATIVE_TURN_STAGE_ORDER`).
- Free-text entry in `game/api.py` `chat` (about line 5433) and structured entry in `action` (about line 4292).
- Contract ownership in `game/ordinary_semantic_ownership.py` and `game/live_resolution.py`.
- Resolver dispatch in `game/contract_adjudication_bridge.py`, `game/noncombat_resolution.py`, `game/social.py`, `game/exploration.py`, and `game/combat.py`.
- Mutation in `game/api.py` `_apply_authoritative_resolution_state_mutation` and the post-narration seam `_apply_post_gm_updates`.
- Authority registry in `game/state_authority.py`.
- Improvisation ledger in `game/bounded_improvisation.py`.
- PR-DE measurements in `artifacts/pr_de_contract_deduplication/PR-DE_affordability_report.md` and `tools/measure_pr_de_affordability.py`.
- PR-DE regression: required suite 326 passed / 27 failed; shared pipeline 41 passed / 24 failed; no new required-suite failures; live calls 0.
- PR-CK notes on action/chat parity and on a persuasion check that returns without a provider call.

Existence of a function is not treated as proof that the behavior is correct. Inherited failures and the observe-only post-narration gateway are recorded as gaps.

## Findings that the experiment must respect

1. Simple NPC turns still serialize about 87 KB of provider context after exact contract deduplication. S1 is 87,583 bytes (11.3% under the 98,773-byte baseline). S2 is 87,152 bytes. C1 is 97,373 bytes. Estimates are `ceil(chars/4)`. They are not provider token bills and they are not prices.

2. The provider is already forbidden, by `game/state_authority.py`, from being a mutation owner. Narration is downstream of resolution on the main path. A later seam, `_post_gm_adoption_gateway`, still records `gateway_policy_enforcement: observe_only` and returns `allow: True`. Shape checks run. Semantic gameplay policy does not.

3. A narrow model proposal already exists. `game/semantic_interpreter.py` `interpret_for_contract` may run when the deterministic fast path abstains and live interpretation is enabled. Its output is a proposal, not a contract. Candidate B generalizes that idea. It does not invent the idea.

4. There is no multi-step plan executor, no tool dispatcher, and no engine undo of an already applied resolver result. The experiment uses a harness snapshot around each existing resolver call. That is specified below. It is not implemented.

5. `chat` advances the world tick and the `time_pressure` clock at the start of every turn, before resolution (`game/api.py` around 5475–5480; `game/world.py` `advance_world_tick`; `game/clocks.py` `advance_clock`). A fair comparison must invoke that policy once, in the harness, for every candidate. A planner or tool must not call it again.

6. Downtime types are classified and then returned as `downtime_engine_not_wired` (`game/noncombat_resolution.py`). World independence in the current engine is the tick (projects, faction pressure, mobile NPC relocation), not a rest or downtime resolver.

7. Combat hit points are mutated inside `game/combat.py` `resolve_attack`. No general inventory-spend API was found. Resource checks in the experiment use combat HP, conditions, and clocks.

8. Narration retry budget is `MAX_TARGETED_RETRY_ATTEMPTS = 2` in `game/gm_retry.py`. PR-CK records that a scene-stall retry can perform two provider calls.

9. Inherited defects are not treated as proof that every deterministic pipeline fails the same way. The movement fixture M1 did not bind an exit. The shared pipeline still has 24 failures. Those are current-tree facts.

## Decision

**A — COMPARISON READY.**

The three candidates are specified against one authority owner, one fixture set, one scoring sheet, and one token-accounting method. The minimum prototype is a harness. It is not a rewrite, and it is not in this cycle.

Recommended next step: build the deterministic preflight harness described in `PR-DF_experiment_design.md`. Run scripted plans and scripted tool transcripts through the existing resolvers. Do not call a provider in that step.

## Document index

| File | Role |
|---|---|
| `PR-DF_current_architecture_map.md` | Phase 1 trace and reuse set |
| `PR-DF_candidate_A.md` | Current pipeline |
| `PR-DF_candidate_B.md` | Planner contract |
| `PR-DF_candidate_C.md` | Tool contract |
| `PR-DF_shared_authority_contract.md` | Shared world rules |
| `PR-DF_improvisation_contract.md` | Ten improvisation cases |
| `PR-DF_experiment_scenarios.md` | Fourteen scenarios |
| `PR-DF_cost_latency_model.md` | Measured A, formulas for B and C |
| `PR-DF_failure_modes.md` | Fourteen failure modes |
| `PR-DF_engine_reuse.md` | Smallest interfaces and effort |
| `PR-DF_experiment_design.md` | Controlled experiment |
| `PR-DF_decision_framework.md` | Weights and disqualifiers |
| `PR-DF_recommendation.md` | Findings, order, keep-or-replace conditions |
| `PR-DF_remaining_risks.md` | What this cycle did not close |
| `changed_files.txt` | Files this cycle added or refreshed |
